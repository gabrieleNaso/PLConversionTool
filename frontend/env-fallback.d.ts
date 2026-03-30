declare const process: {
  env: {
    BACKEND_INTERNAL_URL?: string;
    NEXT_PUBLIC_BACKEND_URL?: string;
    [key: string]: string | undefined;
  };
};
