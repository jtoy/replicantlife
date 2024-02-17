import RenderLevel from '@/components/RenderLevel';

export default async function Page({ params }: { params: { sim_id: string } }) {
 //const data = await getData(params.sim_id);

  return (
    <RenderLevel simId={params.sim_id}/>
  );
}
