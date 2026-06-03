import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineBackend } from '@aws-amplify/backend';
import { Duration } from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Platform } from 'aws-cdk-lib/aws-ecr-assets';
import { auth } from './auth/resource';
import { data } from './data/resource';
import { lambdaRuntimeEnv } from './loadRepoEnv';

const backend = defineBackend({
  auth,
  data,
});

/** Repository root (parent of `web/`). */
const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');

const apiStack = backend.createStack('Nl2sqlApiLambda');
const runtimeEnv = lambdaRuntimeEnv(repoRoot);

const apiFunction = new lambda.DockerImageFunction(apiStack, 'Nl2sqlApiFunction', {
  code: lambda.DockerImageCode.fromImageAsset(repoRoot, {
    file: 'web/amplify/functions/nl2sql-api/Dockerfile',
    platform: Platform.LINUX_AMD64,
  }),
  timeout: Duration.minutes(15),
  memorySize: 2048,
  environment: runtimeEnv,
});

apiFunction.addToRolePolicy(
  new iam.PolicyStatement({
    actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
    resources: ['*'],
  }),
);

const auditBucket = runtimeEnv.AUDIT_S3_BUCKET;
if (auditBucket) {
  apiFunction.addToRolePolicy(
    new iam.PolicyStatement({
      actions: ['s3:GetObject', 's3:PutObject', 's3:ListBucket', 's3:HeadBucket'],
      resources: [`arn:aws:s3:::${auditBucket}`, `arn:aws:s3:::${auditBucket}/*`],
    }),
  );
}

const fnUrl = apiFunction.addFunctionUrl({
  authType: lambda.FunctionUrlAuthType.NONE,
  cors: {
    allowedOrigins: ['*'],
    allowedMethods: [lambda.HttpMethod.GET, lambda.HttpMethod.POST],
    allowedHeaders: ['*'],
  },
  invokeMode: lambda.InvokeMode.BUFFERED,
});

backend.addOutput({
  custom: {
    apiFunctionUrl: fnUrl.url,
    apiFunctionArn: apiFunction.functionArn,
  },
});
