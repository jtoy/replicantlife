'use client';

import React, { useEffect, useState } from 'react';
import RenderLevel from '@/components/RenderLevel';

export default function Page() {
  const [simId, setSimId] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sim_id = params.get('sim_id');
    if (sim_id) {
      setSimId(sim_id);
    }
  }, []);
  
  if (!simId) {
    return null;
  }

  return <RenderLevel simId={simId} />;
}
