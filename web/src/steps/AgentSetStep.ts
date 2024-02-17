import Level from "@/classes/Level";
import { Step, StepJSON } from "./Step";

interface SetConvoDataJSON {
    status: string;
    from: string;
    to: string;
}

export interface AgentSetJSON extends StepJSON {
    attribute_name: string;
    attribute_data: object;
}

export class AgentSetStep extends Step {
    constructor(stepId: number, substepId: number) {
        super(stepId, substepId);
    }

    static fromJSON(json: AgentSetJSON): AgentSetStep {
        if (json.attribute_name == 'convo') {
            const convoData = json.attribute_data as SetConvoDataJSON;
            return new AgentSetConvoStep(json.step, json.substep, convoData.status, convoData.from, convoData.to);
        } else {
            console.log('AgentSetStep.fromJSON() not implemented agent_set type:', json.attribute_name, json.attribute_data);
        }

        return new AgentSetStep(json.step, json.substep);
    }

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    applyStep(levelState: Level) {
        console.log('AgentSetStep.applyStep() not implemented agent_set type');
    }
}

class AgentSetConvoStep extends AgentSetStep {
    status: string;
    fromAgentId: string;
    toAgentId: string;

    constructor(stepId: number, substepId: number, status: string, fromAgentId: string, toAgentId: string) {
        super(stepId, substepId);
        this.status = status;
        this.fromAgentId = fromAgentId;
        this.toAgentId = toAgentId;
    }

    async applyStep(level: Level) {
        const placement = level.findAgentPlacement(this.fromAgentId);
        
        if (!placement) {
            return;
        }

        
        placement.isTalking = false;
    }
}