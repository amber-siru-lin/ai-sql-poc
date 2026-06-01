import type { SemanticLayerMode, SemanticLayerStatus } from "../config";

export type SemanticConsumerPath = {
  path: string;
  role: string;
  exists: boolean;
};

export type SemanticConsumer = {
  id: string;
  name: string;
  mode: SemanticLayerMode | "all";
  description: string;
  paths: SemanticConsumerPath[];
  tools: string[];
  ready: boolean;
  ready_message: string;
  build_artifact?: string;
};

export type SemanticConsumersResponse = {
  repo_root: string;
  semantic_layer: SemanticLayerStatus;
  consumers: SemanticConsumer[];
};
