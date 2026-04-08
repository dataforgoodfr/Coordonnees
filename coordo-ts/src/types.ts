/**
 * Copyright COORDONNÉES 2025, 2026
 * SPDX-License-Identifier: MPL-2.0
 */

// This types comes from the Frictionless Table Schema Specification, used in DataPackages (which is used in coordo-py)
// see https://specs.frictionlessdata.io//table-schema/
export type FrictionlessField = {
  name: string;
  type: string;
  title?: string;
  description?: string;
  format?: string;
  constraints?: Record<string, any>;
  categories?: { value: string; label: string }[];
  [key: string]: any;
};

export type FrictionlessSchema = {
  fields: FrictionlessField[];
  primaryKey?: string[];
  foreignKeys?: Array<{
    fields: string[];
    reference: {
      resource: string;
      fields: string[];
    };
  }>;
  missingValues?: string[];
};

export type LayerMetadata = {
  popup?: {
    trigger: string;
    html?: string;
  };
  schema?: FrictionlessSchema;
};
