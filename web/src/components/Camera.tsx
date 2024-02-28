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
    const [x, setX] = React.useState(0);
    const [y, setY] = React.useState(0);
    const [panning, setPanning] = useState<Panning | undefined>(undefined);

    useEffect(() => {
        if(followAgent) {
            setX(followAgent.position.y * CELL_SIZE);
            setY(followAgent.position.x * CELL_SIZE);
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
            setX(x - dx);
            setY(y - dy);
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