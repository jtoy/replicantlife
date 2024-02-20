import React from "react";
import styles from './Agent.module.css';

const AgentSprite: React.FC<{ agentName: string, isTalking: boolean, isThinking: boolean }> = ({ agentName, isTalking, isThinking }) => {
    return (
        <div className={styles.agent}>
            <div>
                <img 
                    src={`${process.env.NEXT_PUBLIC_BASE_PATH}/images/icons/ChatCircleDots-R.png`} 
                    alt="Talking" 
                    className={`${styles.leftChatIcon} ${isTalking ? '' : styles.hidden}`}
                    width={32}
                    height={32}
                />
                {isThinking && (
                    <img 
                        src={`${process.env.NEXT_PUBLIC_BASE_PATH}/images/icons/lightbulb.gif` }
                        alt="Thinking" 
                        className={styles.thoughtBubbleIcon}
                        width={16}
                        height={16}
                    />
                )}
            </div>
            <img
                src={`${process.env.NEXT_PUBLIC_BASE_PATH}/images/characters/${agentName}.png`} 
                alt={agentName} 
                width={32}
                height={32}
            />
        </div>
    );
};

export default AgentSprite;