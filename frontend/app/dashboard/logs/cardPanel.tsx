import { CardSmall } from "@/components/cards/cardSmall";

type prop = {
  data: {
    raw: { name: string }[];
    alert: { name: string }[];
    block: { name: string }[];
    isActiveRule: { name: string }[];
    patternProfiles: { name: string }[];
  };
  isLoading: boolean;
};

export const CardPanel = ({ data, isLoading }: prop) => {
  if (isLoading) {
    return (
      <>
        <div className="h-32 w-full bg-zinc-800 animate-pulse rounded-xl" />
        <div className="h-32 w-full bg-zinc-800 animate-pulse rounded-xl" />
        <div className="h-32 w-full bg-zinc-800 animate-pulse rounded-xl" />
      </>
    );
  }

  return (
    // <div className="">
    //   {Object.entries(data).map(([key, value]) => {
    //     const metricKey = key as keyof prop["data"];

    //     const config = data[metricKey];
    //     if (!config) return null;

    //     return (
    //       <CardSmall
    //         key={metricKey}
    //         obj={{
    //           header: config.header,
    //           description: config.description,
    //           content: value.length,
    //         }}
    //       />
    //     );
    //   })}
    // </div>
    <h1>hello panel</h1>
  );
};
