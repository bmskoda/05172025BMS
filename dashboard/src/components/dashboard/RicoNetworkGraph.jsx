import { useRef, useEffect, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { ricoLeaders, criminalOrganizations } from '../../data/ricoLeaders';

function buildGraph() {
  const nodes = [];
  const links = [];
  ricoLeaders.forEach(l => { nodes.push({ id: l.id, label: l.name, type: 'leader', risk: l.riskLevel, size: Math.log10(l.financialExposure / 1e9) * 4 }); });
  const orgSet = new Set();
  ricoLeaders.forEach(l => {
    l.linkedEntities.slice(0, 3).forEach(e => {
      const oid = 'org_' + e.replace(/\s/g, '_').toLowerCase();
      if (!orgSet.has(oid)) { orgSet.add(oid); nodes.push({ id: oid, label: e, type: 'organization', risk: 'MEDIUM', size: 6 }); }
      links.push({ source: l.id, target: oid, type: 'controls' });
    });
  });
  criminalOrganizations.slice(0, 6).forEach(c => {
    const cid = 'crim_' + c.name.replace(/\s/g, '_').toLowerCase();
    nodes.push({ id: cid, label: c.name, type: 'criminal', risk: 'CRITICAL', size: 10 });
    ricoLeaders.slice(0, 4).forEach(l => links.push({ source: l.id, target: cid, type: 'funds' }));
  });
  return { nodes, links };
}

export default function RicoNetworkGraph() {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [tooltip, setTooltip] = useState(null);

  const draw = useCallback(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();
    const container = containerRef.current;
    if (!container) return;
    const width = container.clientWidth;
    const height = 500;
    svg.attr('width', width).attr('height', height);

    const { nodes, links } = buildGraph();
    const colorMap = { leader: '#f97316', organization: '#06b6d4', criminal: '#ef4444' };
    const sim = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(80))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => d.size + 4));

    const g = svg.append('g');
    svg.call(d3.zoom().scaleExtent([0.3, 4]).on('zoom', (event) => g.attr('transform', event.transform)));

    const link = g.append('g').selectAll('line').data(links).join('line')
      .attr('stroke', d => d.type === 'funds' ? '#ef444466' : '#06b6d433')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', d => d.type === 'funds' ? '4,2' : 'none');

    const node = g.append('g').selectAll('circle').data(nodes).join('circle')
      .attr('r', d => d.size).attr('fill', d => colorMap[d.type] || '#64748b')
      .attr('stroke', d => d.risk === 'CRITICAL' ? '#ef4444' : 'transparent').attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('mouseover', (event, d) => setTooltip({ x: event.offsetX, y: event.offsetY, label: d.label, type: d.type, risk: d.risk }))
      .on('mouseout', () => setTooltip(null))
      .call(d3.drag().on('start', (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on('end', (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }));

    const labels = g.append('g').selectAll('text').data(nodes.filter(n => n.type === 'leader' || n.type === 'criminal')).join('text')
      .text(d => d.label).attr('font-size', 9).attr('fill', '#94a3b8').attr('text-anchor', 'middle').attr('dy', d => d.size + 12);

    sim.on('tick', () => {
      link.attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y);
      node.attr('cx', d => d.x).attr('cy', d => d.y);
      labels.attr('x', d => d.x).attr('y', d => d.y);
    });
  }, []);

  useEffect(() => { draw(); const ro = new ResizeObserver(draw); if (containerRef.current) ro.observe(containerRef.current); return () => ro.disconnect(); }, [draw]);

  return (
    <section id="network" className="space-y-4">
      <h2 className="text-xl font-bold text-cyan-400 uppercase tracking-wider">RICO Enterprise Network</h2>
      <div className="flex flex-wrap gap-4 text-xs">
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-orange-500" />Leaders</span>
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-cyan-500" />Organizations</span>
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-red-500" />Criminal Orgs</span>
      </div>
      <div ref={containerRef} className="relative rounded-xl border border-cyan-500/10 bg-[#0a0e1a] overflow-hidden">
        <svg ref={svgRef} className="w-full" />
        {tooltip && (
          <div className="pointer-events-none absolute rounded-lg bg-black/90 px-3 py-2 text-xs text-white shadow-xl" style={{ left: tooltip.x + 10, top: tooltip.y - 10 }}>
            <p className="font-bold">{tooltip.label}</p>
            <p className="text-gray-400">{tooltip.type} • {tooltip.risk}</p>
          </div>
        )}
      </div>
    </section>
  );
}
