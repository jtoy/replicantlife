import Level from "@/classes/Level";
import { StepJSON, Step } from "./Step";

export interface ThoughtJSON extends StepJSON {
    content: string;
    importance: number;
    agent_id: string;
    kind: string;
}

export class ThoughtStep extends Step {
    content: string;
    importance: number;
    agentId: string;

    constructor(stepId: number, substepId: number, agentId: string, content: string, importance: number) {
        super(stepId, substepId);
        this.content = content;
        this.importance = importance;
        this.agentId = agentId;
    }

    static fromJSON(json: ThoughtJSON): ThoughtStep {
        return new ThoughtStep(json.step, json.substep, json.agent_id, json.content, json.importance);
    }

    applyStep(levelState: Level) {
        const agent = levelState.findAgentPlacement(this.agentId);

        if (!agent) {
            return;
        }

        agent.think(this);
    }
}