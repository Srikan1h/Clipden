-- ============================================================
-- ClipDen - Supabase Database Schema & Row Level Security
-- ============================================================
-- Creates the snippets table, indexes, timestamp trigger,
-- permissions, and user-isolated Row Level Security policies.
--
-- Authentication: Supabase Anonymous Auth / Authenticated
-- Access: Each user can manage only their own snippets.
-- ============================================================

-- 1. CREATE SNIPPETS TABLE
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.snippets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('manual', 'clipboard')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE
);

-- 2. CREATE INDEXES
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_snippets_user_id
    ON public.snippets (user_id);

CREATE INDEX IF NOT EXISTS idx_snippets_created_at_desc
    ON public.snippets (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_snippets_user_created
    ON public.snippets (user_id, created_at DESC);

-- 3. AUTOMATICALLY UPDATE updated_at
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.clipden_set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    NEW.updated_at = pg_catalog.now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS clipden_updated_at_trigger ON public.snippets;

CREATE TRIGGER clipden_updated_at_trigger
    BEFORE UPDATE ON public.snippets
    FOR EACH ROW
    EXECUTE FUNCTION public.clipden_set_updated_at();

-- 4. ENABLE ROW LEVEL SECURITY
-- ------------------------------------------------------------
ALTER TABLE public.snippets ENABLE ROW LEVEL SECURITY;

-- 5. REMOVE EXISTING POLICIES ON THIS TABLE
-- ------------------------------------------------------------
DO $$
DECLARE
    policy_record RECORD;
BEGIN
    FOR policy_record IN
        SELECT policyname
        FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'snippets'
    LOOP
        EXECUTE format(
            'DROP POLICY IF EXISTS %I ON public.snippets',
            policy_record.policyname
        );
    END LOOP;
END;
$$;

-- 6. CREATE USER-SPECIFIC SECURITY POLICY
-- ------------------------------------------------------------
-- Anonymous Auth users receive the authenticated database role.
-- auth.uid() identifies the currently authenticated user.
-- Each user can SELECT, INSERT, UPDATE, and DELETE only their own records.
CREATE POLICY "ClipDen users manage their own snippets"
ON public.snippets
FOR ALL
TO authenticated
USING (
    (SELECT auth.uid()) = user_id
)
WITH CHECK (
    (SELECT auth.uid()) = user_id
);

-- 7. CONFIGURE DATABASE PERMISSIONS
-- ------------------------------------------------------------
REVOKE ALL ON TABLE public.snippets FROM PUBLIC, anon, authenticated;

GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLE public.snippets
TO authenticated;

GRANT USAGE ON SCHEMA public
TO authenticated;

-- 8. SECURITY VERIFICATION
-- ------------------------------------------------------------
DO $$
BEGIN
    IF NOT (
        SELECT relrowsecurity
        FROM pg_class
        WHERE oid = 'public.snippets'::regclass
    ) THEN
        RAISE EXCEPTION 'ClipDen setup failed: RLS is not enabled.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'snippets'
          AND policyname = 'ClipDen users manage their own snippets'
    ) THEN
        RAISE EXCEPTION 'ClipDen setup failed: RLS policy is missing.';
    END IF;

    RAISE NOTICE 'ClipDen database setup completed successfully.';
END;
$$;
