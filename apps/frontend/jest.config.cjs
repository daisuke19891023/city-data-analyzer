/** @type {import('jest').Config} */
const config = {
    preset: 'ts-jest',
    testEnvironment: 'jsdom',
    roots: ['<rootDir>/src'],
    testMatch: ['**/*.jest.test.ts?(x)'],
    setupFilesAfterEnv: ['<rootDir>/setupTests.ts'],
    moduleNameMapper: {
        '\\.(css|less|scss|sass)$': '<rootDir>/test-file-stub'
    },
    collectCoverageFrom: ['src/**/*.{ts,tsx}']
};

module.exports = config;
