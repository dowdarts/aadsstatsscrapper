import "https://deno.land/x/xhr@0.3.0/mod.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.0';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

Deno.serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    // Use anon key for public read access
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
    );

    const url = new URL(req.url);
    const playerName = url.searchParams.get('player');

    if (playerName) {
      // Get stats for specific player
      const { data: playerStats, error: playerError } = await supabaseClient
        .from('player_stats')
        .select('*')
        .eq('name', playerName)
        .single();

      if (playerError || !playerStats) {
        return new Response(
          JSON.stringify({ error: 'Player not found' }),
          { 
            status: 404, 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          }
        );
      }

      return new Response(
        JSON.stringify({
          player: playerStats.name,
          stats: {
            weighted_3da: playerStats.weighted_3da,
            legs_played: playerStats.legs_played,
            legs_won: playerStats.legs_won,
            total_180s: playerStats.total_180s,
            total_140plus: playerStats.total_140plus,
            total_100plus: playerStats.total_100plus,
            high_finish: playerStats.high_finish,
            events_played: playerStats.events_played,
            is_qualified: playerStats.is_qualified
          }
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Get leaderboard data
    const { data: allPlayers, error: playersError } = await supabaseClient
      .from('player_stats')
      .select('*')
      .order('weighted_3da', { ascending: false });

    if (playersError) {
      console.error('Error fetching player stats:', playersError);
      return new Response(
        JSON.stringify({ error: 'Error fetching stats' }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      );
    }

    // Calculate rankings and format response
    const players = (allPlayers || []).map((player, index) => ({
      rank: index + 1,
      name: player.name,
      weighted_3da: player.weighted_3da || 0,
      legs_played: player.legs_played || 0,
      legs_won: player.legs_won || 0,
      total_180s: player.total_180s || 0,
      total_140plus: player.total_140plus || 0,
      total_100plus: player.total_100plus || 0,
      high_finish: player.high_finish || 0,
      events_played: player.events_played || 0,
      is_qualified: player.is_qualified || false
    }));

    // Get organization info
    const { data: orgData, error: orgError } = await supabaseClient
      .from('organizations')
      .select('name, total_events, current_event')
      .limit(1)
      .single();

    const organization = orgData ? {
      name: orgData.name || 'AADS',
      total_events: orgData.total_events || 7,
      current_event: orgData.current_event || 1
    } : {
      name: 'AADS',
      total_events: 7,
      current_event: 1
    };

    const response = {
      organization,
      stats: {
        total_players: players.length,
        total_legs_played: players.reduce((sum, p) => sum + p.legs_played, 0),
        total_180s: players.reduce((sum, p) => sum + p.total_180s, 0),
        qualified_players: players.filter(p => p.is_qualified).length
      },
      players
    };

    return new Response(
      JSON.stringify(response),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Error in stats function:', error);
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    );
  }
});