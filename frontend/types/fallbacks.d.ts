declare namespace JSX {
  interface IntrinsicElements {
    [elementName: string]: any;
  }
}

declare const process: {
  env: {
    BACKEND_INTERNAL_URL?: string;
    NEXT_PUBLIC_BACKEND_URL?: string;
    [key: string]: string | undefined;
  };
};

declare module "react" {
  export type ReactNode =
    | string
    | number
    | boolean
    | null
    | undefined
    | Iterable<ReactNode>;
}

declare module "next" {
  export interface Metadata {
    title?: string;
    description?: string;
  }
}
