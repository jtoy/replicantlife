import Level from "../classes/Level";
import { Step, StepJSON } from "./Step";

export interface TalkJSON extends StepJSON {
    agent_id: string;
    to_id: string;
    content: string;
}

export class TalkStep extends Step {
    agentId: string;
    toAgentId: string;
    fromAgentName: string;
    toAgentName: string;
    message: string;

    constructor(stepId: number, substepId: number, agentId: string, toAgentId: string, message: string) {
        super(stepId, substepId);
        this.agentId = agentId;
        this.toAgentId = toAgentId;
        this.message = message;
        this.fromAgentName = 'Unknown';
        this.toAgentName = 'Unknown';
    }

    static fromJSON(json: TalkJSON): TalkStep {
        return new TalkStep(json.step, json.substep, json.agent_id, json.to_id, json.content);
    
    }

    applyStep(levelState: Level) {
        const fromAgent = levelState.findAgentPlacement(this.agentId);
        const toAgent = levelState.findAgentPlacement(this.toAgentId);
          
        if(!fromAgent || !toAgent) {
            return;
        }

        this.fromAgentName = fromAgent.agentName;
        this.toAgentName = toAgent.agentName;

        fromAgent.talk(this);
        toAgent.talk(this);
    }
}
