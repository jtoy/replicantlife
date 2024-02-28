"use client";

import Level, { LevelState } from '@/classes/Level';
import styles from './RenderLevel.module.css';
import { useEffect, useRef, useState } from 'react';
import Sidebar from './Sidebar';
import AgentSprite from './AgentSprite';
import Camera from './Camera';
import { Agent } from '@/classes/Agent';
import { CELL_SIZE } from '@/helpers/consts';

async function getData(sim_id: string, fromIndex: number) {
    const redisKey = sim_id;
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/${redisKey}?fromIndex=${fromIndex}`);
  
   
    if (!res.ok) {
      // This will activate the closest `error.js` Error Boundary
      throw new Error('Failed to fetch data')
    }
  
    const data = await res.json();
    const steps = data['steps'];
    const totalSteps = data['totalSteps'];

    return [totalSteps, steps];
  }

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const RenderLevel: React.FC<{simId: string}> = ({ simId }) => {   
    const [isPlaying, setIsPlaying] = useState(true);
    const [followAgent, setFollowAgent] = useState<Agent | undefined>(undefined);
    const [levelState, setLevelState] = useState<LevelState>({stepId: 0, substepId: 0, agents: [],levelImage:"Large"});
    const levelRef = useRef<Level>(new Level([], (newState: LevelState) => {
        setLevelState(newState);
    }));

    useEffect(() => {
        let fetchIndex = 0;
        let isMounted = true;
        const level = levelRef.current;

        const fetchData = async () => {
            if(!level.isPlaying) return;

            const [totalSteps, data] = await getData(simId, fetchIndex);

            if (fetchIndex < totalSteps && isMounted) {
                levelRef.current.addStepsFromJson(data);
                fetchIndex = totalSteps;
            
                if(level.timeline.dataComplete) {
                    clearInterval(interval);
                }
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 12000);

        return () => {
            isMounted = false;
            levelRef.current.destroy();
            clearTimeout(interval);
        }
    }, [simId]);

    useEffect(() => {
        if(levelState.agents.length > 0) {
            setFollowAgent(levelState.agents[0]);
        }
    }, [levelState.agents.length]);
    
    if(!levelState) {
        return (
            <div>Loading...</div>
        )   
    }

    const renderAgents = () => {
        return levelState.agents.map((agent, index) => {
            const x = agent.position.x * CELL_SIZE;
            const y = agent.position.y * CELL_SIZE;

            const style: React.CSSProperties = {
                position: 'absolute',
                top: x,
                left: y,
            };

            return (
                <div key={index} 
                    style={style} 
                    className={styles.placement} 
                    onClick={() => setFollowAgent(agent) }>
                    <AgentSprite agentName={agent.agentName} isTalking={agent.isTalking} isThinking={agent.isThinking} />
                </div>
            );
        });
    };

    return (
        
        <div className={styles.fullScreenContainer}>
            <div className={styles.gameContainer}>

                <Camera followAgent={followAgent} setFollowAgent={setFollowAgent}>
                    <img src={process.env.NEXT_PUBLIC_BASE_PATH +`/images/maps/${levelState.levelImage}.png`} alt="Default Map" />
                    <>
                        {renderAgents()}
                    </>
                </Camera>
                <Sidebar agentPlacement={followAgent} 
                    setFollowAgent={setFollowAgent}
                    isPlaying={isPlaying} 
                    setIsPlaying={setIsPlaying}
                    stepId={levelState.stepId} 
                    substepId={levelState.substepId} 
                    level={levelRef.current} />
            </div>
        </div>
    );
};

export default RenderLevel;