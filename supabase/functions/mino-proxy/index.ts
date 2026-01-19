import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

const MINO_API_URL = 'https://mino.ai/v1/automation/run-sse';

Deno.serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  if (req.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }

  try {
    const { model_name, sources } = await req.json();

    if (!model_name) {
      return new Response(JSON.stringify({ error: 'model_name is required' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const MINO_API_KEY = Deno.env.get('MINO_API_KEY');
    if (!MINO_API_KEY) {
      return new Response(JSON.stringify({ error: 'MINO_API_KEY not configured' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Build the goal prompt for Mino
    const goalPrompt = `Analyze the target leaderboard. Locate the model matching '${model_name}'. Handle dynamic table loading and pagination if necessary. Extract the Overall Rank, Average Score, and three secondary metrics (e.g., Elo, MMLU, Coding). Return a strict JSON array with keys: source, model, rank, score, and secondary_metrics.`;

    const sourceList = sources || ['HuggingFace', 'LMSYS', 'PapersWithCode'];
    
    console.log(`[Mino Proxy] Starting search for model: ${model_name}`);
    console.log(`[Mino Proxy] Sources: ${sourceList.join(', ')}`);

    // Make the SSE request to Mino
    const response = await fetch(MINO_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': MINO_API_KEY,
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({
        goal: goalPrompt,
        sources: sourceList,
        model_name: model_name,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[Mino Proxy] Mino API error: ${response.status} - ${errorText}`);
      return new Response(JSON.stringify({ 
        error: `Mino API error: ${response.status}`,
        details: errorText 
      }), {
        status: response.status,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Stream the SSE response back to the client
    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();
    const encoder = new TextEncoder();

    // Process the stream in the background
    EdgeRuntime.waitUntil((async () => {
      try {
        const reader = response.body?.getReader();
        if (!reader) {
          await writer.write(encoder.encode(`data: ${JSON.stringify({ type: 'error', message: 'No response body' })}\n\n`));
          await writer.close();
          return;
        }

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          
          if (done) {
            console.log('[Mino Proxy] Stream completed');
            await writer.write(encoder.encode(`data: ${JSON.stringify({ type: 'done' })}\n\n`));
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              console.log(`[Mino Proxy] Event: ${data.substring(0, 100)}...`);
              await writer.write(encoder.encode(`data: ${data}\n\n`));
            } else if (line.trim()) {
              await writer.write(encoder.encode(`data: ${JSON.stringify({ type: 'log', message: line })}\n\n`));
            }
          }
        }
      } catch (error) {
        console.error('[Mino Proxy] Stream error:', error);
        await writer.write(encoder.encode(`data: ${JSON.stringify({ type: 'error', message: String(error) })}\n\n`));
      } finally {
        await writer.close();
      }
    })());

    return new Response(readable, {
      headers: {
        ...corsHeaders,
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    console.error('[Mino Proxy] Error:', error);
    return new Response(JSON.stringify({ error: String(error) }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
