import { Step } from "@/steps/Step";
import { TalkStep } from "@/steps/TalkStep";
import { ThoughtStep } from "@/steps/ThoughtStep";
import { AgentSetStep } from "@/steps/AgentSetStep";

export interface GridPosition {
    x: number;
    y: number;
}

export class Agent {
    position: GridPosition;
    steps: Step[];
    agentName: string;
    agentId: string;
    isTalking: boolean;
    isThinking: boolean;
    status: string

    constructor(position: GridPosition, agentName: string, agentId: string, status: string) {
        this.position = position;
        this.agentName = agentName;
        this.agentId = agentId;
        this.isTalking = false;
        this.isThinking = false;
        this.status = status;
        this.steps = [];
    }

    readyForNextStep() {
        return !this.isThinking;
    }

    talk(talkStep: TalkStep) {
        this.isTalking = true;
        this.steps.push(talkStep);
    }

    think(thoughtStep: ThoughtStep) {
        this.isThinking = true;
        this.steps.push(thoughtStep);

        setTimeout(() => {
            this.isThinking = false;
        }, 1500);
    }

    agentSet(agentSetStep: AgentSetStep) {
        this.status = "dead";
        this.steps.push(agentSetStep);
    }
}
