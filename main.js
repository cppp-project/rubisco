"use strict";

import * as core from "@actions/core";
import * as exec from "@actions/exec";
import * as fs from "fs";
import * as sevenZipBinary from "7zip-bin"
import fetch from "node-fetch";
import path from "path";

// Repository name.
const repoName = "cppp-project/cppp-repoutils";

/**
 * Detect latest release version.
 *
 * @returns {Promise<String>} The latest release version.
 */
async function getLatestReleaseVersion() {
    const apiUrl = `https://api.github.com/repos/${ repoName }/releases/latest`;
    const response = await fetch(apiUrl);
    const json = await response.json();

    if (json.message === "Not Found") {
        const errorMessage = `Latest release of ${ repoName } not found.`;
        core.setFailed(errorMessage);

        return Promise.reject(errorMessage);
    }
    core.info(`Detected latest release version: ${ json.tag_name }`);

    return Promise.resolve(json.tag_name);
}

/**
 * Detect latest release 7-Zip archive URL.
 *
 * @param {String} version The version of the release.
 * @returns {Promise<String>} The latest release 7-Zip archive URL.
 */
async function getReleaseArchiveUrl(version) {
    const apiUrl = `https://api.github.com/repos/${ repoName }/releases/tags/${ version }`;
    const response = await fetch(apiUrl);
    const json = await response.json();
    const assets = json.assets;
    if(!assets) {
        const errorMessage = `Assets of ${ repoName } not found.`;
        core.setFailed(errorMessage);

        return Promise.reject(errorMessage);
    }

    const archive = assets.find(asset => asset.name.endsWith(".7z"));
    if(!archive) {
        const errorMessage = `7-Zip archive of ${ repoName } not found.`;
        core.setFailed(errorMessage);

        return Promise.reject(errorMessage);
    }

    const archiveUrl = archive.browser_download_url;
    if(!archiveUrl) {
        const errorMessage = `URL of 7-Zip archive of ${ repoName } not found.`;
        core.setFailed(errorMessage);

        return Promise.reject(errorMessage);
    }

    core.info(`Detected latest release archive URL: ${ archiveUrl }`);

    return Promise.resolve(archiveUrl);
}

/**
 * Download a file.
 * @param {String} url The URL to download.
 * @param save_path The path to save the file.
 * @returns {Promise<void>}
 */
async function downloadFile(url, save_path) {
    // Fetch archive.
    core.info(`Downloading archive: ${ url }`);
    const response = await fetch(url);
    const arrayBuffer = await response.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    // Write buffer to file.
    fs.writeFileSync(save_path, buffer);
    core.info(`Archive saved to: ${ save_path }`);
}

/**
 * Extract a 7-Zip archive.
 *
 * @param {String} archiveFile The path to the archive file.
 * @param {String} releaseDir Possible release directory in the archive.
 * @returns {Promise<String>} The release directory path in the archive.
 * @summary This function only can extract C++ Plus Project release archive.
 */
async function extract7ZipArchive(archiveFile, releaseDir) {
    // Extract archive.
    core.info(`Extracting archive: ${ archiveFile }`);
    await exec.exec(sevenZipBinary.path7za, ["x", archiveFile]);
    core.info(`Archive extracted.`);
    var directory = releaseDir
    if(!fs.existsSync(directory)) {
        core.warning(`We can't find the directory "${ directory }" in the archive, \
maybe the archive is not a standard C++ Plus Project release archive.`);
        const files = fs.readdirSync(".");
        for(const file of files) {
            if(fs.statSync(file).isDirectory()) {
                directory = file;
                break;
            }
        }
    }
    core.info(`Release directory: ${ directory }`);

    return Promise.resolve(directory);
}

/**
 * Main entry.
 */
async function run() {
    try {
        // Fetch archive.
        const latestReleaseVersion = await getLatestReleaseVersion();
        const latestReleaseArchiveUrl = await getReleaseArchiveUrl(latestReleaseVersion)
        await downloadFile(latestReleaseArchiveUrl, "package.7z");

        // Extracting archive.
        const possibleReleaseDir = repoName.split("/")[1] + "-" + latestReleaseVersion;
        const releaseDir = await extract7ZipArchive("package.7z", possibleReleaseDir);
        const binDir = path.join(releaseDir, "bin");
        if(!fs.existsSync(binDir)) {
            const errorMessage = `Extracted binary directory not found: ${ binDir }`;
            core.setFailed(errorMessage);

            return Promise.reject(errorMessage);
        }
        core.info(`Binary directory: ${ binDir }`);

        // Add binary directory to PATH.
        core.addPath(fs.realpathSync(binDir));

        // Extracted, removing unused archive.
        core.info("Removing archive ...");
        fs.unlinkSync("package.7z");
    }
    catch (error) {
        core.setFailed(error.message);
    }
}

// Run the program.
await run();
