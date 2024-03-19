import React from "react";
import styles from './Agent.module.css';

const AgentSprite: React.FC<{ agentName: string, isTalking: boolean, isThinking: boolean, status: string, map: string }> = ({ agentName, isTalking, isThinking, status, map }) => {
    let agentImage = `${process.env.NEXT_PUBLIC_BASE_PATH}/images/characters/${agentName}.png`;
    console.log("AgentSpriteeee status = ", status);

    let size = { width: 32, height: 32 };
    if (map == "stage") {
        size = { width: 150, height: 150 }; // Set a different size for agents if map is "stage"
    }

    // Check if agentName matches "Zombie" using regex
    if (/Zombie/.test(agentName)) {
        agentImage = `${process.env.NEXT_PUBLIC_BASE_PATH}/images/characters/Zombie_1.png`;
    }
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
                        src={`${process.env.NEXT_PUBLIC_BASE_PATH}/images/icons/lightbulb.gif`}
                        alt="Thinking"
                        className={styles.thoughtBubbleIcon}
                        width={16}
                        height={16}
                    />
                )}
                {status == "dead" && (
                    <img
                        src={`${process.env.NEXT_PUBLIC_BASE_PATH}/images/icons/dead.png`}
                        alt="Dead"
                        className={styles.deadIcon}
                        width={16}
                        height={16}
                    />
                )}
            </div>
            <img
                src={agentImage}
                alt={agentName}
                width={size.width}
                height={size.height}
            />
        </div>
    );
};

export default AgentSprite;
