import React from 'react';
import styles from './TalkBubble.module.css';
import 'animate.css';

type TalkBubbleProps = {
    direction: 'inbound' | 'outbound';
    fromName: string;
    toName: string;
    message: string;
};

const TalkBubble: React.FC<TalkBubbleProps> = ({
    direction,
    fromName,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    toName,
    message,
}) => {
    const side = direction === 'inbound' ? 'left' : 'right';
    return (
        <div className={`${styles.bubble} ${styles[side]} animate__animated animate__slideInDown`}>
            {/*<div className={`${styles.talkBubble} ${styles[direction]}`}>*/}
            {/*<div className={styles.name}>{fromName}</div>
            <div className={styles.name}>{toName}</div>*/}
            <b>{fromName}: </b>
            <span className={styles.message}>{message}</span>
        </div>
    );
};

export default TalkBubble;