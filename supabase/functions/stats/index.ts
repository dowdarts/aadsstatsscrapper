import "https://deno.land/x/xhr@0.3.0/mod.ts";

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
    const url = new URL(req.url);
    const playerName = url.searchParams.get('player');

    // Demo data that matches the expected format
    const demoPlayers = [
      {
        name: "John Doe",
        rank: 1,
        weighted_3da: 85.2,
        total_legs: 24,
        total_180s: 8,
        total_140s: 15,
        total_100s: 45,
        highest_finish: 170,
        events_played: [1, 2, 3],
        qualified: true,
        total_average: 85.2,
        total_140_plus: 15
      },
      {
        name: "Jane Smith", 
        rank: 2,
        weighted_3da: 82.7,
        total_legs: 22,
        total_180s: 6,
        total_140s: 12,
        total_100s: 38,
        highest_finish: 156,
        events_played: [1, 2],
        qualified: true,
        total_average: 82.7,
        total_140_plus: 12
      },
      {
        name: "Mike Johnson",
        rank: 3, 
        weighted_3da: 79.8,
        total_legs: 20,
        total_180s: 4,
        total_140s: 10,
        total_100s: 32,
        highest_finish: 144,
        events_played: [1, 3],
        qualified: false,
        total_average: 79.8,
        total_140_plus: 10
      }
    ];

    if (playerName) {
      // Get stats for specific player
      const player = demoPlayers.find(p => p.name === playerName);
      if (!player) {
        return new Response(
          JSON.stringify({ 
            success: false,
            error: 'Player not found' 
          }),
          { 
            status: 404, 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          }
        );
      }

      return new Response(
        JSON.stringify({
          success: true,
          player: player
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Return leaderboard data in expected format
    const response = {
      success: true,
      series_info: {
        name: "Atlantic Amateur Darts Series",
        total_events: 7,
        qualifying_events: 6,
        championship_event: 7
      },
      leaderboard: demoPlayers,
      players: demoPlayers, // For compatibility with frontend
      total_players: demoPlayers.length,
      last_updated: new Date().toISOString()
    };

    return new Response(
      JSON.stringify(response),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Error in stats function:', error);
    return new Response(
      JSON.stringify({ 
        success: false,
        error: 'Internal server error',
        message: error.message 
      }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    );
  }
});