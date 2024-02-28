import { MatrixSetStep } from "@/steps/MatrixSetStep";
import { MatrixInitStep } from "@/steps/MatrixInitStep";

import { Step } from "../steps/Step";
import Level from "./Level";

export class Timeline {
  level: Level;
  steps: Step[];
  currentStep: Step | undefined;
  currentStepIndex: number;
  currentSubstep: Step | undefined;
  dataComplete: boolean;

  constructor(level: Level) {
    this.level = level;
    this.steps = [];
    this.currentStepIndex = -1;

    this.dataComplete = false;
  }

  get length() {
    return this.steps.length;
  }

  get currentStepId(){
    return this.currentStep?.stepId ?? 0;
  }

  get currentSubstepId(){
    return this.currentStep?.substepId ?? -1;
  }

  get nextStep(): Step | undefined {
    return this.steps[this.currentStepIndex + 1];
  }

  atEnd() {
    return this.currentStepIndex === this.steps.length - 1;
  }

  newStepIsPending() {
    if(!this.nextStep) return false;
    if(!this.currentStep) return false;

    return  this.nextStep.stepId > this.currentStep.stepId;
  }

  advanceOneSubstep(): Step {
    if(!this.nextStep) throw new Error("No next step");

    this.currentStep = this.nextStep;
    this.currentStepIndex++;
    return this.currentStep;
  }

  applyOneSubstep() {
    if (!this.nextStep) return false;

    const step = this.advanceOneSubstep();
    step.applyStep(this.level);
  }

  applyOneStep() {
    if(!this.atEnd() && this.newStepIsPending()) {
      this.applyOneSubstep();
    }

    while(!this.atEnd() && !this.newStepIsPending()) {
      this.applyOneSubstep();
    }
  }
  
  addSteps(steps: Step[]) {
    steps.forEach(step => {
      this.steps.push(step);
      if (step instanceof MatrixSetStep) {
        if ((step as MatrixSetStep).status === "complete") {
          this.dataComplete = true;
        }
      }
      if (step instanceof MatrixInitStep) {
        step.applyStep(this.level);
      }
      
    });
    //console.log(this.steps);
  }

  rewind() {
    this.currentStep = undefined;
    this.currentStepIndex = -1;
  }

  empty() {
    this.steps = [];
    this.currentStep = undefined;
  }
}