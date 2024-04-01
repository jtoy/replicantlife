'use client';

import React, { useEffect, useState } from 'react';
import RenderLevel from '@/components/RenderLevel';

export default function Page() {
  const [simId, setSimId] = useState<string | null>(null);
  const [map, setMapName] = useState<string | null>(null);
  const [img, setImgName] = useState<string | null>(null);
  const [hidePanel, setHidePanel] = useState<boolean>(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sim_id = params.get('sim_id');
    const map = params.get('map');
    const img = params.get('img');
    const hidePanel = params.get('hide');
    if (sim_id) {
      setSimId(sim_id);
    }
    if (map) {
      setMapName(map);
    }
    if (img) {
      setImgName(img);
    }
    if (hidePanel === '1') {
        setHidePanel(true);
    }
  }, []);

  if (!simId) {
    return null;
  }

  return <RenderLevel simId={simId} map={map} img={img} hidePanel={hidePanel} />
}
