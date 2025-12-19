import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from 'jsr:@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface PlayerStats {
  name: string;
  total_games: number;
  total_wins: number;
  win_percentage: number;
  points_scored_01: number;
  darts_thrown_01: number;
  average_01: number;
  first_nine_avg: number;
  count_180s: number;
  count_140_plus: number;
  count_100_plus: number;
  highest_score: number;
  checkout_efficiency: string;
  checkout_opportunities: number;
  checkouts_hit: number;
  highest_checkout: number;
  avg_finish: number;
  card_link: string;
}

Deno.serve(async (req: Request) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const body = await req.json();
    console.log('Request body:', JSON.stringify(body));
    
    const { event_url, event_name } = body;

    if (!event_url || !event_name) {
      console.error('Missing required fields:', { event_url, event_name });
      return new Response(
        JSON.stringify({ 
          success: false, 
          error: `Missing required fields. event_url: ${event_url ? 'present' : 'missing'}, event_name: ${event_name ? 'present' : 'missing'}`,
          received: body
        }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Get user from auth
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      { global: { headers: { Authorization: req.headers.get('Authorization')! } } }
    );

    const { data: { user } } = await supabaseClient.auth.getUser();
    if (!user) {
      return new Response(
        JSON.stringify({ success: false, error: 'Not authenticated' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Extract event ID from URL
    const eventIdMatch = event_url.match(/event\/([^\/]+)/);
    if (!eventIdMatch) {
      return new Response(
        JSON.stringify({ success: false, error: 'Invalid event URL format' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }
    const eventId = eventIdMatch[1];

    // Step 1: Extract match URLs from API2
    console.log(`Extracting match URLs for event ${eventId}...`);
    const api2Response = await fetch(`https://tv.dartconnect.com/api2/event/${eventId}/matches`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });

    if (!api2Response.ok) {
      throw new Error(`API2 request failed: ${api2Response.status}`);
    }

    const api2Data = await api2Response.json();
    const matchIds: string[] = [];

    // Extract match IDs from segments
    if (api2Data.payload?.sections) {
      for (const section of api2Data.payload.sections) {
        if (section.segments) {
          for (const segment of section.segments) {
            if (segment.match_id) {
              matchIds.push(segment.match_id);
            }
          }
        }
      }
    }

    if (matchIds.length === 0) {
      return new Response(
        JSON.stringify({ success: false, error: 'No matches found in event' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    console.log(`Found ${matchIds.length} matches`);

    // Step 2: Scrape each match with comprehensive stats
    let successful = 0;
    let failed = 0;
    const errors: string[] = [];
    const playerSummary: Record<string, { match_count: number; count_180s: number }> = {};

    for (const matchId of matchIds) {
      try {
        console.log(`Scraping match ${matchId}...`);
        
        // Fetch /players/ endpoint
        const playersResponse = await fetch(`https://recap.dartconnect.com/players/${matchId}`);
        if (!playersResponse.ok) {
          throw new Error(`Failed to fetch players data: ${playersResponse.status}`);
        }

        const playersHtml = await playersResponse.text();
        const playersMatch = playersHtml.match(/data-page="([^"]+)"/);
        if (!playersMatch) {
          throw new Error('Could not find Inertia data in players page');
        }

        const playersData = JSON.parse(playersMatch[1].replace(/&quot;/g, '"'));
        const players = playersData.props?.players || [];

        // Fetch /counts/ endpoint
        const countsResponse = await fetch(`https://recap.dartconnect.com/counts/${matchId}`);
        if (!countsResponse.ok) {
          throw new Error(`Failed to fetch counts data: ${countsResponse.status}`);
        }

        const countsHtml = await countsResponse.text();
        const countsMatch = countsHtml.match(/data-page="([^"]+)"/);
        if (!countsMatch) {
          throw new Error('Could not find Inertia data in counts page');
        }

        const countsData = JSON.parse(countsMatch[1].replace(/&quot;/g, '"'));
        const distribution = countsData.props?.distribution || [];
        const first_nine = countsData.props?.first_nine || [];
        const checkout_stats = countsData.props?.checkout_stats || [];

        // Process each player
        for (let i = 0; i < players.length; i++) {
          const player = players[i];
          const firstNineStats = first_nine[i] || {};
          const checkoutData = checkout_stats[i] || {};
          const dist = distribution[i] || {};

          // Calculate 140+ from distribution
          let count_140_plus = 0;
          if (dist['140']) count_140_plus += dist['140'];
          if (dist['141']) count_140_plus += dist['141'];
          if (dist['160']) count_140_plus += dist['160'];
          if (dist['171']) count_140_plus += dist['171'];
          // Add 180s
          const count_180s = dist['180'] || 0;
          count_140_plus += count_180s;

          // Prepare record
          const record = {
            user_id: user.id,
            name: player.name,
            match_id: matchId,
            event_name: event_name,
            legs_won: player.total_wins,
            legs_played: player.total_games,
            average: player.average_01,
            first_nine_avg: firstNineStats.average || null,
            count_180s: count_180s,
            count_140_plus: count_140_plus,
            count_100_plus: (dist['100'] || 0) + count_140_plus,
            highest_score: Math.max(...Object.keys(dist).map(k => parseInt(k) || 0)),
            checkout_efficiency: checkoutData.efficiency || null,
            checkout_opportunities: checkoutData.opportunities || 0,
            checkouts_hit: checkoutData.hit || 0,
            highest_checkout: checkoutData.highest || null,
            avg_finish: checkoutData.average || null,
            card_link: player.card_link || null,
          };

          // Upsert to Supabase
          const { error } = await supabaseClient
            .from('aads_players')
            .upsert(record, {
              onConflict: 'user_id,event_name,match_id,name'
            });

          if (error) {
            throw new Error(`Supabase upsert failed: ${error.message}`);
          }

          // Track player summary
          if (!playerSummary[player.name]) {
            playerSummary[player.name] = { match_count: 0, count_180s: 0 };
          }
          playerSummary[player.name].match_count++;
          playerSummary[player.name].count_180s += count_180s;
        }

        successful++;
        
        // Delay between matches
        await new Promise(resolve => setTimeout(resolve, 2000));

      } catch (error) {
        failed++;
        const errorMsg = `Match ${matchId}: ${error.message}`;
        console.error(errorMsg);
        errors.push(errorMsg);
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        total_matches: matchIds.length,
        successful,
        failed,
        total_players: Object.keys(playerSummary).length,
        players: playerSummary,
        errors: errors.length > 0 ? errors : undefined,
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Error:', error);
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
