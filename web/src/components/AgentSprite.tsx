import React from "react";
import Image from "next/image";
import styles from './Agent.module.css';

const AgentSprite: React.FC<{ agentName: string, isTalking: boolean, isThinking: boolean }> = ({ agentName, isTalking, isThinking }) => {
    return (
        <div className={styles.agent}>
            <div>
                <Image 
                    src="/images/icons/ChatCircleDots-R.png" 
                    alt="Talking" 
                    className={`${styles.leftChatIcon} ${isTalking ? '' : styles.hidden}`}
                    width={32}
                    height={32}
                />
                {isThinking && (
                    <Image 
                        src="/images/icons/lightbulb.gif" 
                        alt="Thinking" 
                        className={styles.thoughtBubbleIcon}
                        width={16}
                        height={16}
                    />
                )}
            </div>
            <Image 
                src={`/images/characters/${agentName}.png`} 
                alt={agentName} 
                width={32}
                height={32}
            />
        </div>
    );
};

export default AgentSprite;