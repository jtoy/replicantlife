import Level from "../classes/Level";

export interface StepJSON {
    step: number;
    substep: number;
    step_type: string ;
}

export abstract class Step {
    stepId: number;
    substepId: number;

    constructor(stepId: number, substepId: number) {
        this.stepId = stepId;
        this.substepId = substepId;
    }

    abstract applyStep(levelState: Level): void;

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    static fromJSON(json: StepJSON): Step {
        throw new Error('Step.fromJSON() not implemented');
    }
}


