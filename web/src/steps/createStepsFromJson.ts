import { NewAgentJSON, NewAgentStep } from "./NewAgentStep";
import { MoveJSON, MoveStep } from "./MoveStep";
import { TalkJSON, TalkStep } from "./TalkStep";
import { StepJSON, Step } from "./Step";
import { AgentSetJSON, AgentSetStep } from "./AgentSetStep";
import { MatrixSetJSON, MatrixSetStep } from "./MatrixSetStep";
import { ThoughtJSON, ThoughtStep } from "./ThoughtStep";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function createStepsFromJson(stepsData: StepJSON[]): Step[] {
    const steps: Step[] = [];

    for (const stepData of stepsData) {
        switch (stepData.step_type) {
            case 'agent_init':
                steps.push(NewAgentStep.fromJSON(stepData as NewAgentJSON));
                break;
            case 'move':
                steps.push(MoveStep.fromJSON(stepData as MoveJSON));
                break;
            case 'talk':
                steps.push(TalkStep.fromJSON(stepData as TalkJSON));
                break;
            case 'agent_set':
                steps.push(AgentSetStep.fromJSON(stepData as AgentSetJSON));
                break;
            case 'matrix_set':
                steps.push(MatrixSetStep.fromJSON(stepData as MatrixSetJSON));
                break;
            case 'add_memory': {
                const meta = stepData as ThoughtJSON;
                if (meta.kind === 'meta') {
                    steps.push(ThoughtStep.fromJSON(meta));
                }
                break;
            }
            default:
                break;
        }
    }
    
    return steps;
}


export default createStepsFromJson;