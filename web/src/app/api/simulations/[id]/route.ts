
import { getRedisClient } from "@/lib/redisClient";
import { NextRequest } from "next/server";

// Initialize Redis connection
const redis = getRedisClient();

// Check if Redis client is connected
redis.on('connect', () => {
  const redisDetails = `Connected to Redis server at ${redis.options.host}:${redis.options.port}`;
  console.log(redisDetails);
});

// Check for errors during connection
redis.on('error', (err) => {
  console.error('Error connecting to Redis server:', err);
});


// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function getStepsFromRedis(id: string, prevStartIndex: number, chunkSize: number): Promise<[number, any]> {
  try {
    const totalSteps = await redis.llen(id);

    if (totalSteps - prevStartIndex <= 0) {
      console.log("all steps have been fetched", prevStartIndex)
      return [totalSteps, []];
    }

    let startIndex = 0;
    if (totalSteps - prevStartIndex <= chunkSize) {
      startIndex = -1; // last chunk, we start at index 0
    }
    else {
      startIndex = totalSteps - prevStartIndex - chunkSize;
    }

    const stepsData = await redis.lrange(id, startIndex + 1, totalSteps - prevStartIndex);
    if (!stepsData) {
      throw new Error('No data found for steps');
    }

    return [totalSteps, stepsData];

  } catch (error) {
    console.error('Failed to fetch steps from Redis:', error);
    throw new Error('Failed to fetch steps data');
  }
}



// eslint-disable-next-line @typescript-eslint/no-explicit-any
function uiSteps(step: any) {
  let keep = false;
  const keepTypes = ['talk', 'agent_set', 'move', 'matrix_set', 'agent_init'];

  if (keepTypes.includes(step.step_type)) {
    keep = true;
  }

  if (step.step_type === 'add_memory') {
    if (step.kind === 'meta') {
      keep = true;
    }
  }

  return keep;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function sortSteps(a: any, b: any) {
  if (a.step === b.step) {
    return a.substep - b.substep;
  }

  return a.step - b.step;
}

// Return a list of `params` to populate the [slug] dynamic segment
export async function generateStaticParams() {
  return [{ id: 'skip' }];
}

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const id = params.id;
  if (id === 'skip') {
    return Response.json([]);
  }

  const fromIndex = Number(request.nextUrl.searchParams.get('fromIndex')) || 0;
  const chunkSize = 1000; // Adjust chunk size as needed

  const [totalSteps, allSteps] = await getStepsFromRedis(id, fromIndex, chunkSize);

  let steps = allSteps.map((step: string) => JSON.parse(step));
  steps = steps.filter(uiSteps);
  steps = steps.sort(sortSteps);

  return Response.json({ steps: steps, totalSteps: totalSteps });
}
