import Level from "@/classes/Level";
import { StepJSON, Step } from "./Step";

export interface MatrixInitJSON extends StepJSON {
    status: string;
}

export class MatrixInitStep extends Step {
    // status: string;

    constructor(stepId: number, substepId: number) {
        super(stepId, substepId);
        // this.status = status;
    }

    static fromJSON(json: MatrixInitJSON): MatrixInitStep {
        return new MatrixInitStep(json.step, json.substep);
    }

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    applyStep(level: Level) {
        level.simulationStarted = true;
    }
}