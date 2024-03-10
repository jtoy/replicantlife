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
    status: string;
    agent_id: string;
}

export class AgentSetStep extends Step {
    agentStatus: string;
    agentId: string;

    constructor(stepId: number, substepId: number, agentStatus: string, agentId: string) {
        super(stepId, substepId);
        this.agentStatus = agentStatus;
        this.agentId = agentId;
    }

    static fromJSON(json: AgentSetJSON): AgentSetStep {
        if (json.attribute_name == 'convo') {
            const convoData = json.attribute_data as SetConvoDataJSON;
            return new AgentSetConvoStep(json.step, json.substep, convoData.status, convoData.from, convoData.to, json.status, json.agent_id);
        } else if (json.attribute_name == 'status') {
            return new AgentSetStep(json.step, json.substep, json.status, json.agent_id);
        } else {
            console.log('AgentSetStep.fromJSON() not implemented agent_set type:', json.attribute_name, json.attribute_data);
        }

        return new AgentSetStep(json.step, json.substep, json.status, json.agent_id);
    }

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    applyStep(levelState: Level) {
        console.log('AgentSetStep.applyStep() not implemented agent_set type');

        const agent = levelState.findAgentPlacement(this.agentId);

        if (!agent) {
            return;
        }

        agent.agentSet(this);
    }
}

class AgentSetConvoStep extends AgentSetStep {
    status: string;
    fromAgentId: string;
    toAgentId: string;

    constructor(stepId: number, substepId: number, status: string, fromAgentId: string, toAgentId: string, agentStatus: string, agentId: string) {
        super(stepId, substepId, agentStatus, agentId);
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