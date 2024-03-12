import { Agent, GridPosition } from "@/classes/Agent";
import Level from "../classes/Level";
import { Step } from "./Step";
import { StepJSON } from "./Step";

export interface NewAgentJSON extends StepJSON {
    x: number;
    y: number;
    name: string;
    agent_id: string;
    status: string;
    description: string;
    goal: string;
}

export class NewAgentStep extends Step {
    agentId: string;
    agentName: string;
    position: GridPosition;
    agentStatus: string;
    agentDescription: string;
    agentGoal: string;

    constructor(stepId: number, substepId: number, agentId: string, agentName: string, position: GridPosition, agentStatus: string, agentDescription: string, agentGoal: string) {
        super(stepId, substepId);
        this.agentId = agentId;
        this.agentName = agentName;
        this.position = position;
        this.agentStatus = agentStatus;
        this.agentDescription = agentDescription;
        this.agentGoal = agentGoal;
    }

    applyStep(level: Level) {
        const placement = new Agent(this.position, this.agentName, this.agentId, this.agentStatus, this.agentDescription, this.agentGoal);

        level.agents.push(placement);
    }

    static fromJSON(json: NewAgentJSON): NewAgentStep {
        const position: GridPosition = { x: json.y, y: json.x };
        return new NewAgentStep(json.step, json.substep, json.agent_id, json.name, position, json.status, json.description, json.goal);
    }
}