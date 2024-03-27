"use client";

import Level, { LevelState } from '@/classes/Level';
import styles from './RenderLevel.module.css';
import React from 'react';
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
const RenderLevel: React.FC<{ simId: string, map?: string | null, img?: string | null }> = ({ simId, map, img }) => {
    const [isPlaying, setIsPlaying] = useState(true);
    const [followAgent, setFollowAgent] = useState<Agent | undefined>(undefined);
    const [levelState, setLevelState] = useState<LevelState>({ stepId: 0, substepId: 0, agents: [] });
    const [fetchIndex, setFetchIndex] = useState(0);
    const [initialFetchDone, setInitialFetchDone] = useState(false);
    const chunkSize = 1000; // Adjust chunk size as needed

    const levelRef = useRef<Level>(new Level([], (newState: LevelState) => {
        setLevelState(newState);
    }));

    const fetchData = async () => {
        const [totalSteps, data] = await getData(simId, fetchIndex);
        setFetchIndex(fetchIndex + chunkSize);
        console.log(totalSteps);

        if (!initialFetchDone) {
            setInitialFetchDone(true);
        }

        levelRef.current.addStepsFromJson(data);

        // if (fetchIndex >= totalSteps) {
        //     setIsPlaying(false); // or perform any other action when all data is fetched
        // }
    };

    useEffect(() => {
        // let isMounted = true;
        if (!initialFetchDone) {
            fetchData(); // Fetch immediately for the first time
        } else {
            const interval = setInterval(fetchData, 10000); // Subsequent fetches at 20-second intervals

            return () => {
                // isMounted = false;
                clearInterval(interval);
            };
        }
    }, [simId, fetchIndex]);


    useEffect(() => {
        if (levelState.agents.length > 0) {
            setFollowAgent(levelState.agents[0]);
        }
    }, [levelState.agents.length]);

    if (!levelState) {
        return (
            <div>Loading...</div>
        )
    }

    const renderAgents = () => {
        if (map == "stage") {
            console.log("STEPID", levelState.stepId);
            console.log("AGENT LENGTH", levelState.agents.length);
            return levelState.agents.map((agent, index) => {
                const x = agent.position.x;
                const y = agent.position.y;

                const style: React.CSSProperties = {
                    position: 'relative',
                    cursor: 'pointer',
                    top: x,
                    left: y,
                };

                return (
                    <div key={index}
                        style={style}
                        className={styles.placement}>
                        <AgentSprite agentName={agent.agentName} isTalking={agent.isTalking} isThinking={agent.isThinking} status={agent.status} map={map} />
                    </div>
                );
            });

        }
        return levelState.agents.map((agent, index) => {
            const x = agent.position.x * CELL_SIZE;
            const y = agent.position.y * CELL_SIZE;

            const style: React.CSSProperties = {
                position: 'absolute',
                top: x,
                left: y,
                cursor: 'pointer',
            };

            return (
                <div key={index}
                    style={style}
                    className={styles.placement}
                    onClick={() => setFollowAgent(agent)}>
                    <AgentSprite agentName={agent.agentName} isTalking={agent.isTalking} isThinking={agent.isThinking} status={agent.status} map=""/>
                </div>
            );
        });
    };

    if (map == "stage") {
        return (
            <div className={styles.fullScreenContainer}>
                <img
                    src={img ? (process.env.NEXT_PUBLIC_CONTENT_DIRECTORY + "/images/maps/" + img) : (process.env.NEXT_PUBLIC_BASE_PATH + "/images/maps/Large.png")}
                    alt="Stage Map"
                    className={styles.stageImg}
                />
                <div className={styles.agentContainer}>
                    <>
                        {renderAgents()}
                    </>
                </div>
                <Sidebar agentPlacement={followAgent}
                    setFollowAgent={setFollowAgent}
                    isPlaying={isPlaying}
                    setIsPlaying={setIsPlaying}
                    stepId={levelState.stepId}
                    substepId={levelState.substepId}
                    level={levelRef.current}
                    simId={simId}
                    toggleAudio={toggleAudio}
                    audioPlayings={audioPlaying} />
            </div>
        );
    }

    return (

        <div className={styles.fullScreenContainer}>
            <div className={styles.gameContainer}>

                <Camera followAgent={followAgent} setFollowAgent={setFollowAgent}>
                    <img
                        src={img ? (process.env.NEXT_PUBLIC_CONTENT_DIRECTORY + "/images/maps/" + img) : (process.env.NEXT_PUBLIC_BASE_PATH + "/images/maps/Large.png")}
                        alt="Default Map"
                    />
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