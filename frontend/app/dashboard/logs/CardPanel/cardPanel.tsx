import { CardSmall } from "@/components/cards/cardSmall";
import styles from "./style.module.scss";

type prop = {
  data: card[] | undefined;
  isLoading: boolean;
  isError: boolean;
  error: null | Error;
};

type card = {
  id: string;
  header: string;
  count: number;
  description: string;
};

export const CardPanel = ({ data, isLoading, isError, error }: prop) => {
  if (isLoading || data === undefined) {
    return (
      <div className={styles.Panel}>
        <div className="h-32  bg-zinc-800 animate-pulse rounded-xl" />
        <div className="h-32  bg-zinc-800 animate-pulse rounded-xl" />
        <div className="h-32  bg-zinc-800 animate-pulse rounded-xl" />
      </div>
    );
  }

  if (isError && error) {
    return (
      <>
        <CardSmall variant="minimal" title="Error" content={error?.message} />
      </>
    );
  }

  return (
    <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-5 w-full">
      {data?.map((item) => (
        <CardSmall
          variant="minimal"
          key={item.id}
          title={item.header}
          description={item.description}
          content={item.count}
          className="text-center lg:text-start"
        />
      ))}
    </div>
  );
};
