/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import React, { useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import { GraphData } from '../lib/api';

// Dynamically import ForceGraph2D with no SSR
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
    ssr: false
});

interface GraphNode {
    id: string;
    label: string;
    color: string;
    x?: number;
    y?: number;
    __bckgDimensions?: number[];
    [key: string]: unknown; // Allow other properties from force-graph
}

interface GraphLink {
    source: GraphNode | string;
    target: GraphNode | string;
    label?: string;
    [key: string]: unknown;
}

interface Props {
    data: GraphData;
    darkMode: boolean;
    highlightedNodes?: string[];
}

const GraphVisualization: React.FC<Props> = ({ data, darkMode, highlightedNodes = [] }) => {
    const graphRef = useRef<any>(null);

    useEffect(() => {
        // Refresh graph when data or theme changes
        if (graphRef.current) {
            graphRef.current.d3ReheatSimulation();
        }
    }, [data, darkMode, highlightedNodes]);

    return (
        <div className="h-full w-full">
            <ForceGraph2D
                ref={graphRef}
                graphData={{
                    nodes: data.nodes,
                    links: data.edges // Map edges to links for force-graph
                }}
                nodeLabel="label"
                nodeColor={(node: any) => {
                    if (highlightedNodes.length > 0 && !highlightedNodes.includes(node.id)) {
                        return darkMode ? '#1e293b' : '#e2e8f0'; // Dimmed color
                    }
                    return node.color;
                }}
                backgroundColor={darkMode ? "#0f172a" : "#ffffff"} // slate-900 vs white
                linkColor={(link: any) => {
                    if (highlightedNodes.length > 0) {
                        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                        const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                        if (!highlightedNodes.includes(sourceId) || !highlightedNodes.includes(targetId)) {
                            return darkMode ? "#1e293b" : "#f1f5f9"; // Very dim link
                        }
                    }
                    return darkMode ? "#475569" : "#cbd5e1";
                }}

                // Custom Node Rendering (Minimal + Label)
                nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
                    const n = node as GraphNode;
                    if (n.x === undefined || n.y === undefined) return;

                    const isHighlighted = highlightedNodes.length === 0 || highlightedNodes.includes(n.id);
                    const isDimmed = !isHighlighted;

                    const label = n.label;
                    const fontSize = (isHighlighted ? 12 : 10) / globalScale;
                    ctx.font = `${fontSize}px Sans-Serif`;
                    const textWidth = ctx.measureText(label).width;
                    const bckgDimensions = [textWidth, fontSize].map(num => num + fontSize * 0.2); // some padding

                    // Draw Node (Circle)
                    ctx.beginPath();
                    ctx.arc(n.x, n.y, isHighlighted ? 5 : 3, 0, 2 * Math.PI, false);
                    ctx.fillStyle = isDimmed ? (darkMode ? '#334155' : '#cbd5e1') : n.color;
                    ctx.fill();

                    // Halo for highlighted nodes
                    if (isHighlighted && highlightedNodes.length > 0) {
                        ctx.beginPath();
                        ctx.arc(n.x, n.y, 8, 0, 2 * Math.PI, false);
                        ctx.strokeStyle = n.color;
                        ctx.lineWidth = 1 / globalScale;
                        ctx.stroke();
                    }

                    // Draw Label
                    if (isHighlighted || globalScale > 2) { // Only show labels for highlighted nodes or when zoomed in
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillStyle = isDimmed ? (darkMode ? '#475569' : '#94a3b8') : (darkMode ? '#f1f5f9' : '#1e293b');
                        ctx.fillText(label, n.x, n.y + (isHighlighted ? 8 : 6));
                    }

                    n.__bckgDimensions = bckgDimensions; // to re-use in nodePointerAreaPaint
                }}

                // Custom Link Rendering (Edge Label)
                linkCanvasObject={(link: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
                    const l = link as any; // Force graph link object has source/target as objects after init
                    const start = l.source as GraphNode;
                    const end = l.target as GraphNode;

                    if (!start.x || !start.y || !end.x || !end.y) return;

                    const isHighlighted = highlightedNodes.length === 0 || (highlightedNodes.includes(start.id) && highlightedNodes.includes(end.id));

                    // Draw Line
                    ctx.beginPath();
                    ctx.moveTo(start.x, start.y);
                    ctx.lineTo(end.x, end.y);
                    ctx.strokeStyle = isHighlighted ? (darkMode ? "#475569" : "#cbd5e1") : (darkMode ? "#1e293b" : "#f1f5f9");
                    ctx.lineWidth = 1 / globalScale;
                    ctx.stroke();

                    // Draw Label (Relationship Type)
                    if (l.label && isHighlighted) {
                        const textPos = {
                            x: start.x + (end.x - start.x) / 2,
                            y: start.y + (end.y - start.y) / 2
                        };

                        const relLabel = l.label;
                        const fontSize = 10 / globalScale;
                        ctx.font = `${fontSize}px Sans-Serif`;

                        // Background for text to make it readable
                        const textWidth = ctx.measureText(relLabel).width;
                        ctx.fillStyle = darkMode ? '#0f172a' : '#ffffff';
                        ctx.fillRect(textPos.x - textWidth / 2 - 1, textPos.y - fontSize / 2 - 1, textWidth + 2, fontSize + 2);

                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillStyle = darkMode ? '#94a3b8' : '#64748b'; // slate-400 vs slate-500
                        ctx.fillText(relLabel, textPos.x, textPos.y);
                    }
                }}

                onNodeClick={(node: any) => {
                    // Focus on node
                    const n = node as GraphNode;
                    if (n.x && n.y) {
                        graphRef.current?.centerAt(n.x, n.y, 1000);
                        graphRef.current?.zoom(8, 2000);
                    }
                }}
            />
        </div>
    );
};

export default GraphVisualization;
