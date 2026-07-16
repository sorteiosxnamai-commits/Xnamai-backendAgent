-- Isolamento incremental de atendimentos, conversas, funil e estado Mercos.
-- Nenhuma tabela e criada e nenhum backfill e executado.

DO $$
DECLARE
  table_name TEXT;
  table_names CONSTANT TEXT[] := ARRAY[
    'atendimentos',
    'conversas',
    'mensagens',
    'canais',
    'campanhas',
    'funil_estagios',
    'funil_negocios',
    'chatbot_fluxos',
    'integracoes',
    'mercos_sync_logs'
  ];
BEGIN
  IF to_regclass('public.workspaces') IS NULL THEN
    RAISE EXCEPTION 'Pre-condicao ausente: public.workspaces nao existe';
  END IF;

  FOREACH table_name IN ARRAY table_names LOOP
    IF to_regclass(format('public.%I', table_name)) IS NULL THEN
      CONTINUE;
    END IF;

    EXECUTE format(
      'ALTER TABLE public.%I ADD COLUMN IF NOT EXISTS workspace_id UUID',
      table_name
    );
    EXECUTE format(
      'CREATE INDEX IF NOT EXISTS %I ON public.%I(workspace_id)',
      'idx_' || table_name || '_workspace_id',
      table_name
    );
  END LOOP;
END $$;

DO $$
DECLARE
  table_name TEXT;
  workspace_attribute SMALLINT;
  table_names CONSTANT TEXT[] := ARRAY[
    'atendimentos',
    'conversas',
    'mensagens',
    'canais',
    'campanhas',
    'funil_estagios',
    'funil_negocios',
    'chatbot_fluxos',
    'integracoes',
    'mercos_sync_logs'
  ];
BEGIN
  FOREACH table_name IN ARRAY table_names LOOP
    IF to_regclass(format('public.%I', table_name)) IS NULL THEN
      CONTINUE;
    END IF;

    SELECT attnum
      INTO workspace_attribute
    FROM pg_attribute
    WHERE attrelid = format('public.%I', table_name)::regclass
      AND attname = 'workspace_id'
      AND NOT attisdropped;

    IF NOT EXISTS (
      SELECT 1
      FROM pg_constraint
      WHERE conrelid = format('public.%I', table_name)::regclass
        AND contype = 'f'
        AND confrelid = 'public.workspaces'::regclass
        AND conkey = ARRAY[workspace_attribute]::smallint[]
    ) THEN
      EXECUTE format(
        'ALTER TABLE public.%I ADD CONSTRAINT %I FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id)',
        table_name,
        table_name || '_workspace_id_fkey'
      );
    END IF;
  END LOOP;
END $$;

NOTIFY pgrst, 'reload schema';
