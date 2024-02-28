import React, { useEffect, useState } from 'react';
import { Agent } from '@/classes/Agent';
import { CELL_SIZE } from '@/helpers/consts';

interface CameraProps {
    followAgent: Agent | undefined,
    setFollowAgent: (agent: Agent | undefined) => void;
    children: React.ReactNode;
}

interface Panning {
    startX: number;
    startY: number;
}

const Camera: React.FC<CameraProps> = ({ setFollowAgent, followAgent, children }) => {
    const transformOffsetX = -75 * CELL_SIZE;
    const transformOffsetY = -75 * CELL_SIZE;
    const zoomSpeed = 0.02;

    const [scale, setScale] = React.useState(1);
    const [x, setHorizontal] = React.useState(0); // Changed setX to setHorizontal to avoid confusing names
    const [y, setVertical] = React.useState(0); // Changed setY to setVertical to avoid confusing names
    const [panning, setPanning] = useState<Panning | undefined>(undefined);

    useEffect(() => {
        if(followAgent) {
            setHorizontal(followAgent.position.y * CELL_SIZE); // setHorizontal (setX) should use the y position to correctly follow the agent
            setVertical(followAgent.position.x * CELL_SIZE); // setVertical (setY) should use the x position to correctly follow the agent
        }
    }, [followAgent?.position.x, followAgent?.position.y]);

    const handleWheel = (e: React.WheelEvent) => {
        const newScale = (e.deltaY>0) ? scale * (1 - zoomSpeed) : scale * (1 + zoomSpeed);
        setScale(newScale);
    };

    const handleMouseDown = (e: React.MouseEvent) => {
        e.preventDefault();
        setFollowAgent(undefined);
        setPanning({startX: e.clientX, startY: e.clientY});
    };

    const handleMouseUp = () => {
        setPanning(undefined);
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        if(panning) {
            const dx = e.clientX - panning.startX;
            const dy = e.clientY - panning.startY;
            setHorizontal(x - dx);
            setVertical(y - dy);
            setPanning({startX: e.clientX, startY: e.clientY});
        }
    };

    const cameraStyle: React.CSSProperties = {
        transform: `scale(${scale}) translate3d(${-x-transformOffsetX}px, ${-y-transformOffsetY}px, 0)`,
        transition: followAgent ? 'transform 1.5s linear' : 'none'
    };

    return (
        <div style={cameraStyle} 
            onWheel={handleWheel} 
            onMouseDown={handleMouseDown}
            onMouseUp={handleMouseUp}
            onMouseMove={handleMouseMove}>
            {children}
        </div>
    );
};

export default Camera;