# Multi-Tenant Setup Instructions

## Database Schema Setup

Run these SQL commands in your Supabase SQL Editor:
https://supabase.com/dashboard/project/kswwbqumgsdissnwuiab/sql/new

### 1. Create Organizations Table

```sql
-- Create organizations table to store user/org settings
CREATE TABLE IF NOT EXISTS organizations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
  organization_name TEXT NOT NULL,
  logo_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- Users can only see and edit their own organization
CREATE POLICY "Users can view own organization"
  ON organizations FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update own organization"
  ON organizations FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own organization"
  ON organizations FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```

### 2. Create Display Settings Table

```sql
-- Create display_settings table for customization
CREATE TABLE IF NOT EXISTS display_settings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
  
  -- Event Configuration
  series_count INTEGER DEFAULT 3,
  singles_count INTEGER DEFAULT 5,
  
  -- Stats Display Options (JSON for flexibility)
  visible_stats JSONB DEFAULT '{"averages": true, "high_out": true, "ton_plus": true, "highest_score": true, "champions": true}'::jsonb,
  
  -- Color Customization
  primary_color TEXT DEFAULT '#00d4ff',
  secondary_color TEXT DEFAULT '#ffffff',
  background_color TEXT DEFAULT '#1a1a1a',
  text_color TEXT DEFAULT '#ffffff',
  border_color TEXT DEFAULT '#00d4ff',
  header_bg_color TEXT DEFAULT '#000000',
  
  -- Layout Options
  show_organization_logo BOOLEAN DEFAULT true,
  show_sponsors BOOLEAN DEFAULT true,
  sponsor_position TEXT DEFAULT 'bottom', -- 'top', 'bottom', 'sidebar'
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE display_settings ENABLE ROW LEVEL SECURITY;

-- Users can only see and edit their own settings
CREATE POLICY "Users can view own settings"
  ON display_settings FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update own settings"
  ON display_settings FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own settings"
  ON display_settings FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Public can view settings for display pages
CREATE POLICY "Public can view all settings"
  ON display_settings FOR SELECT
  TO anon
  USING (true);
```

### 3. Create Sponsors Table

```sql
-- Create sponsors table for partner/sponsor logos
CREATE TABLE IF NOT EXISTS sponsors (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  logo_url TEXT NOT NULL,
  website_url TEXT,
  display_order INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE sponsors ENABLE ROW LEVEL SECURITY;

-- Users can manage their own sponsors
CREATE POLICY "Users can view own sponsors"
  ON sponsors FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sponsors"
  ON sponsors FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sponsors"
  ON sponsors FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own sponsors"
  ON sponsors FOR DELETE
  USING (auth.uid() = user_id);

-- Public can view active sponsors for display pages
CREATE POLICY "Public can view active sponsors"
  ON sponsors FOR SELECT
  TO anon
  USING (is_active = true);
```

### 4. Update Events Table - Add user_id

```sql
-- Add user_id column to existing events table
ALTER TABLE events ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Update RLS policies for events table
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON events;
DROP POLICY IF EXISTS "Enable read access for all users" ON events;
DROP POLICY IF EXISTS "Enable delete for authenticated users" ON events;

-- New policies with user_id isolation
CREATE POLICY "Users can insert own events"
  ON events FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own events"
  ON events FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own events"
  ON events FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Public can view all events for display pages
CREATE POLICY "Public can view all events"
  ON events FOR SELECT
  TO anon
  USING (true);
```

### 5. Update Event Winners Table - Add user_id

```sql
-- Add user_id column to event_winners table
ALTER TABLE event_winners ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Update RLS policies
DROP POLICY IF EXISTS "Enable read access for all users" ON event_winners;

CREATE POLICY "Users can view own winners"
  ON event_winners FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

-- Public can view all winners for display pages
CREATE POLICY "Public can view all winners"
  ON event_winners FOR SELECT
  TO anon
  USING (true);
```

## Storage Setup

### Create Storage Buckets

1. Go to: https://supabase.com/dashboard/project/kswwbqumgsdissnwuiab/storage/buckets

2. Create two public buckets:
   - **Name**: `organization-logos`
     - Public: Yes
     - Allowed MIME types: `image/png,image/jpeg,image/svg+xml`
     - Max file size: 2MB
   
   - **Name**: `sponsor-logos`
     - Public: Yes
     - Allowed MIME types: `image/png,image/jpeg,image/svg+xml`
     - Max file size: 2MB

### Set Storage Policies

Run in SQL Editor:

```sql
-- Organization logos - users can upload their own
CREATE POLICY "Users can upload own org logo"
  ON storage.objects FOR INSERT
  TO authenticated
  WITH CHECK (
    bucket_id = 'organization-logos' AND
    auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Users can update own org logo"
  ON storage.objects FOR UPDATE
  TO authenticated
  USING (
    bucket_id = 'organization-logos' AND
    auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Users can delete own org logo"
  ON storage.objects FOR DELETE
  TO authenticated
  USING (
    bucket_id = 'organization-logos' AND
    auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Anyone can view org logos"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'organization-logos');

-- Sponsor logos - same pattern
CREATE POLICY "Users can upload own sponsor logos"
  ON storage.objects FOR INSERT
  TO authenticated
  WITH CHECK (
    bucket_id = 'sponsor-logos' AND
    auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Users can update own sponsor logos"
  ON storage.objects FOR UPDATE
  TO authenticated
  USING (
    bucket_id = 'sponsor-logos' AND
    auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Users can delete own sponsor logos"
  ON storage.objects FOR DELETE
  TO authenticated
  USING (
    bucket_id = 'sponsor-logos' AND
    auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Anyone can view sponsor logos"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'sponsor-logos');
```

## Enable Email Signup

1. Go to: https://supabase.com/dashboard/project/kswwbqumgsdissnwuiab/auth/providers
2. Enable "Email" provider if not already enabled
3. Configure email templates under Auth > Email Templates
4. Consider disabling email confirmation for easier testing (can re-enable later)

## After Setup

Once database is configured:
1. Existing users will need to be migrated or create new accounts
2. Each new user automatically gets organization and display_settings records created
3. Users access their display page at: `stats-display.html?user=<user_id>`
4. Admin interface shows settings panel for full customization
