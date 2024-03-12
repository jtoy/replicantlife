import { Agent } from '@/classes/Agent';
import React, { useEffect, useState } from 'react';
import styles from './Sidebar.module.css';
import AgentSprite from './AgentSprite';
import { TalkStep } from '@/steps/TalkStep';
import { ThoughtStep } from '@/steps/ThoughtStep';
import TalkBubble from './TalkBubble';
import ThoughtBubble from './ThoughtBubble';
import Level from '@/classes/Level';

interface SidebarProps {
    agentPlacement: Agent | undefined;
    setFollowAgent: React.Dispatch<React.SetStateAction<Agent | undefined>>;
    isPlaying: boolean
    setIsPlaying: React.Dispatch<React.SetStateAction<boolean>>;
    stepId: number;
    substepId: number;
    level: Level;
}

const Sidebar: React.FC<SidebarProps> = (
    { 
        agentPlacement, 
        setFollowAgent,
        isPlaying,
        setIsPlaying,
        stepId, 
        substepId, 
        level 
    }) => {
    
    const [showThoughts, setShowThoughts] = useState(true);
    

    useEffect(() => {
        let interval: NodeJS.Timeout;
        
        if (isPlaying) {
            level.nextStep();
            interval = setInterval(() => {
                level.nextStep();
            }, 1500); // adjust the interval as needed
        }
        return () => {
            if (interval) {
                clearInterval(interval);
            }
        };
    }, [isPlaying]);

    const handleRewind = (): void => {
        setIsPlaying(false);
        setFollowAgent(undefined);
        level.rewind();
        level.isPlaying = false;
    }

    const handlePause = (): void => {
        setIsPlaying(false);
        level.isPlaying = false;
    }

    const handlePlay = (): void => {
        setIsPlaying(true);
        level.isPlaying = true;
        //level.nextStep();
    }

    const handleStep = (): void => {
        level.nextStep();
    }

    const handleGoto = (): void => {
        setIsPlaying(false);
        const userInput = prompt("Step #", stepId.toString()); 
        const targetStep = parseInt(userInput!);
        if (targetStep > stepId) {
            level.advanceTo(targetStep);
        } else if (targetStep < stepId) {
            setFollowAgent(undefined);
            level.rewind();
            level.advanceTo(targetStep);
        }
        level.isPlaying = false;
    }
    
    const renderTimeline = () => {
        if(!agentPlacement) return null;

        const steps = agentPlacement.steps.toReversed();

        return steps.map(step => {
            const stepString = `${step.stepId}-${step.substepId}`;
            if (step instanceof TalkStep) {
                const talkStep = step as TalkStep;
                const direction = agentPlacement.agentId === talkStep.agentId ? 'outbound' : 'inbound';
                return <TalkBubble key={stepString} direction={direction} fromName={talkStep.fromAgentName} toName={talkStep.toAgentName} message={talkStep.message} />;
            
            }
            if (step instanceof ThoughtStep && showThoughts) {
                const thoughtStep = step as ThoughtStep;
                return <ThoughtBubble key={stepString} content={thoughtStep.content} />;
            }
            
            return null;
        });
        
    };

    const renderControls = () => {
        return(
            <div className={styles.gameControls}>
                <div>
                    Step: {stepId}
                </div>
                <span style={{ display: 'none' }}>{substepId}</span>
                <div className={styles.buttons}>
                    <button onClick={handleRewind}>Rewind</button>
                    <button onClick={handlePause} disabled={!isPlaying}>Pause</button>
                    <button onClick={handlePlay} disabled={isPlaying}>Play</button>
                    <button onClick={handleStep} disabled={isPlaying}>Step</button>
                    <button onClick={handleGoto} disabled={isPlaying}>Goto</button>
                </div>

            </div>
        )
    };

    return (
        // JSX for the Sidebar component goes here
        <div className={styles.sidebar}>
            {renderControls()}
            {agentPlacement && <div className={styles.agentInfoContainer}>
                <div className={styles.agentModule}>
                    <AgentSprite agentName={agentPlacement.agentName} isTalking={false} isThinking={false} status={agentPlacement.status} />
                    <div className={styles.agentName}>{agentPlacement.agentName}</div>
                    <div className={styles.thoughtSelector}>
                        <label>
                            <input type="checkbox" checked={showThoughts} onChange={() => setShowThoughts(!showThoughts)} />
                            Show Thoughts
                        </label>
                    </div>
                    <button onClick={() => setFollowAgent(undefined)} className={styles.closeButton}>
                        Close
                    </button>
                </div>
                <hr />
                <div>
                    <p className={styles.agentInfo}><strong>Description:</strong> {agentPlacement.description}</p>
                    <p className={styles.agentInfo}><strong>Goal:</strong> {agentPlacement.goal}</p>
                </div>
            </div>
            }
            <>
                {renderTimeline()}
            </>
        </div>
    );
};

export default Sidebar;