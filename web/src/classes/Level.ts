import { Agent } from "@/classes/Agent";
import createStepsFromJson from "@/steps/createStepsFromJson";
import { Timeline } from './Timeline';

export interface LevelState {
    agents: Agent[];
    stepId: number;
    substepId: number;
}

export const findAgentName = (agentId: string, agents: Agent[]) => {
    const agent = agents.find(agent => agent.agentId === agentId);
    return agent?.agentName || 'Unknown';
};

export default class Level {
    agents: Agent[];
    onEmit: (newLevelState: LevelState) => void;
    timeline: Timeline;
    subStepId: number = 1;
    debug: boolean = false;
    simulationComplete: boolean = false;
    isPlaying: boolean = true;

    constructor(placements: Agent[], onEmit: (newLevelState: LevelState) => void) {
        this.agents = placements;
        this.onEmit = onEmit;
        this.timeline = new Timeline(this);
    }

    get stepId() {
        return this.timeline.currentStepId;
    }

    get substepId() {
        return this.timeline.currentSubstepId;
    }

    destroy() {
        
        this.timeline.empty();
        this.agents = [];
    }

    get levelState() {
        return {
            agents: this.agents,
            stepId: this.stepId,
            substepId: this.substepId
        };
    }

    findAgentPlacement(agentId: string): Agent | undefined {
        return this.agents.find(placement => placement.agentId === agentId);
    }

    rewind() {
        this.timeline.rewind()
        this.agents = [];
        this.onEmit(this.levelState);
    }

    nextStep() {
        this.timeline.applyOneStep();
        this.onEmit(this.levelState);
    }
    
    advanceTo(targetStepId: number) {
        while(this.stepId < targetStepId) {
            this.nextStep();
        }
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    addStepsFromJson(data: any) {
        
        this.timeline.addSteps(createStepsFromJson(data));
    }
}