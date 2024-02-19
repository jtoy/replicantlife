import React from 'react';
import styles from './ThoughtBubble.module.css';

type ThoughtBubbleProps = {
    content: string;
};

const ThoughtBubble: React.FC<ThoughtBubbleProps> = ({
    content
}) => {

    return (
        <div className={`${styles.thought}`}>
            {content}
        </div>
    );
};

export default ThoughtBubble;