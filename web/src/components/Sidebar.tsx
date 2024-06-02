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
    hidePanel: boolean;
    level: Level;
    simId: string;
}

const Sidebar: React.FC<SidebarProps> = (
    { 
        agentPlacement, 
        setFollowAgent,
        isPlaying,
        setIsPlaying,
        stepId, 
        substepId, 
        level,
        simId,
        hidePanel
    }) => {
    
        const [showThoughts, setShowThoughts] = useState(true);
        const [isPlayAudio, setIsPlayAudio] = useState(true);
        const [audioQueue, setAudioQueue] = useState<Promise<string>[]>([]);
        const [audioPlaying, setAudioPlaying] = useState<boolean>(false);
        const browserLanguage = navigator.language;

        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const minimal_audio_delay = 500; // delay in between playing audio clips
        //hidePanel = false;
        //WTF pass this



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

    const fetchAudioData = async (sim_id: string, step_id: number, substep_id: number, agent_name: string, lang: string, content: string): Promise<string> => {
    try {
        const res = await fetch(
            `${process.env.NEXT_PUBLIC_ASSET_DOMAIN}/audio?mid=${sim_id}&step=${step_id}&substep=${substep_id}&agent=${agent_name}&lang=${lang}&c=${btoa(content)}`,
            { mode: 'cors' }
        );
        if (!res.ok) {
            throw new Error('Failed to fetch data');
        }

        const audioBlob = await res.blob();
        const audioUrl = URL.createObjectURL(audioBlob);

        // Preload the audio file
        const audio = new Audio(audioUrl);
        audio.preload = 'auto';
        audio.load();

        return audioUrl;
    } catch (error) {
        console.error('Error fetching audio:', error);
        return "";
    }
};


    const addToAudioQueue = (audioClipUrl: Promise<string>) => {
        setAudioQueue((oldQueue) => [...oldQueue, audioClipUrl]);
    };

    const playAudio = async (audioClipUrl: Promise<string>) => {
        console.log("BEFORE LENGTH", audioQueue.length)
        setAudioPlaying(true);
        const audio = new Audio(await audioClipUrl);
        audio.onended = () => {
            setAudioQueue((oldQueue) => oldQueue.slice(1));
            console.log("AFTER LENGTH", audioQueue.length)
            setAudioPlaying(false);
        };
        audio.play();
    };

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const stopAudio = (audio: HTMLAudioElement) => {
        if (audio) {
            audio.pause();
            audio.currentTime = 0;
        }
    };

    useEffect(() => {
        if (isPlaying && agentPlacement && !audioPlaying && audioQueue.length > 0) {
            playAudio(audioQueue[0]);
        }
    }, [agentPlacement, isPlaying, audioQueue, audioPlaying]);

    useEffect(() => {
        if (agentPlacement && isPlayAudio) {
            const steps = agentPlacement.steps.filter(
                step => step.stepId >= stepId
            );
            steps.forEach(step => {
                if (step instanceof TalkStep) {
                    const talkStep = step as TalkStep;
                    addToAudioQueue(fetchAudioData(simId, talkStep.stepId, talkStep.substepId, talkStep.fromAgentName, browserLanguage,talkStep.message));

                    return;
                }
                if (showThoughts && step instanceof ThoughtStep) {
                    const thoughtStep = step as ThoughtStep;
                    addToAudioQueue(fetchAudioData(simId, thoughtStep.stepId, thoughtStep.substepId, thoughtStep.agentId, browserLanguage,thoughtStep.content));
                    return;
                }
            });
        }

        if (!agentPlacement || !isPlayAudio) {
            setAudioQueue([]);
        }

    }, [agentPlacement, showThoughts, isPlayAudio, stepId, substepId]);

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
        if (hidePanel) {
          return null;
        }

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
        if (hidePanel) {
          return null;
        }
        return(
            <div className={styles.gameControls}>
                <div className={styles.stepAndAudio}>
                    Step: {stepId}
                    {process.env.NEXT_PUBLIC_ALLOW_AUDIO === "true" && <div>
                        <label>
                            <input type="checkbox" checked={isPlayAudio} onChange={() => setIsPlayAudio(!isPlayAudio)} />
                            Play Audio
                        </label>
                    </div>}
                    {level.simulationStarted && <div id="simulationStarted" style={{ display: 'none' }}>
                        Simulation Started!
                    </div>}
                    {level.simulationComplete && <div id="simulationComplete" style={{ display: 'none' }}>
                        Simulation Complete!
                    </div>}
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
    if (hidePanel) {
      return null;
    }

    return (
        // JSX for the Sidebar component goes here
        <div className={styles.sidebar}>
            {renderControls()}
            {agentPlacement && <div className={styles.agentInfoContainer}>
                <div className={styles.agentModule}>
                    <AgentSprite agentName={agentPlacement.agentName} isTalking={false} isThinking={false} status={agentPlacement.status} map="" />
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
