import { useState, useEffect, useCallback } from "react";

interface LoaderProps {
    onComplete: () => void;
    progress: number; // 0-100
}

export function Loader({ onComplete, progress }: LoaderProps) {
    const [hidden, setHidden] = useState(false);

    const handleComplete = useCallback(() => {
        setHidden(true);
        setTimeout(onComplete, 800);
    }, [onComplete]);

    useEffect(() => {
        if (progress >= 100) {
            setTimeout(handleComplete, 300);
        }
    }, [progress, handleComplete]);

    return (
        <div className={`seq-loader ${hidden ? "hidden" : ""}`}>
            <div className="seq-loader-text">Generating Authorization Sequence</div>
            <div className="seq-loader-bar-track">
                <div
                    className="seq-loader-bar"
                    style={{ width: `${progress}%` }}
                />
            </div>
        </div>
    );
}
