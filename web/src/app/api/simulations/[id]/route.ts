
import { getRedisClient } from "@/lib/redisClient";
import { NextRequest } from "next/server";

// Initialize Redis connection
const redis = getRedisClient();

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function getStepsFromRedis(id: string, fromIndex: number): Promise<[number, any]> {
  try {
    const totalSteps = await redis.llen(id);

    if(totalSteps - fromIndex <= 0){
      return [totalSteps, []];
    }

    const stepsData = await redis.lrange(id, 0, totalSteps - fromIndex - 1);
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

  if(keepTypes.includes(step.step_type)) {
    keep = true;
  }

  if(step.step_type === 'add_memory') {
    if(step.kind === 'meta') {
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

export async function GET(
    request: NextRequest,
    { params }: { params: { id: string } }
  
    ) {
        const id = params.id;
        const fromIndex = Number(request.nextUrl.searchParams.get('fromIndex')) || 0;

        const [totalSteps, allSteps] = await getStepsFromRedis(id, fromIndex);
      
        let steps = allSteps.map((step: string) => JSON.parse(step));
        steps = steps.filter(uiSteps);
        steps = steps.sort(sortSteps);
             
        return Response.json({ steps: steps, totalSteps: totalSteps });
}