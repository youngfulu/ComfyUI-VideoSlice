import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";
import { api } from "../../scripts/api.js";

/**
 * Like core IMAGEUPLOAD but for the `video` combo + mp4/mov accept (uses /upload/image, server saves any bytes to input).
 */
ComfyWidgets.VIDEOUPLOAD = function (node, inputName, inputData, app) {
	const wname = inputData[1]?.widget ?? "video";
	const videoWidget = node.widgets.find((w) => w.name === wname);
	if (!videoWidget) {
		console.error("VIDEOUPLOAD: no widget named", wname);
		return {};
	}

	async function uploadFile(file, updateNode) {
		try {
			const body = new FormData();
			body.append("image", file);
			const resp = await api.fetchApi("/upload/image", {
				method: "POST",
				body,
			});
			if (resp.status === 200) {
				const data = await resp.json();
				let path = data.name;
				if (data.subfolder) path = data.subfolder + "/" + path;
				if (!videoWidget.options.values.includes(path)) {
					videoWidget.options.values.push(path);
					videoWidget.options.values.sort();
				}
				if (updateNode) {
					videoWidget.value = path;
				}
			} else {
				alert(resp.status + " - " + resp.statusText);
			}
		} catch (error) {
			alert(error);
		}
	}

	const fileInput = document.createElement("input");
	Object.assign(fileInput, {
		type: "file",
		accept: "video/mp4,video/quicktime,video/x-msvideo,.mp4,.mov",
		style: "display: none",
		onchange: async () => {
			if (fileInput.files.length) {
				await uploadFile(fileInput.files[0], true);
			}
		},
	});
	document.body.append(fileInput);

	const uploadWidget = node.addWidget("button", inputName, "video", () => {
		fileInput.click();
	});
	uploadWidget.label = "choose file to upload";
	uploadWidget.serialize = false;

	node.onDragOver = function (e) {
		if (e.dataTransfer && e.dataTransfer.items) {
			const f = [...e.dataTransfer.items].find((x) => x.kind === "file");
			return !!f;
		}
		return false;
	};

	node.onDragDrop = function (e) {
		let handled = false;
		for (const file of e.dataTransfer.files) {
			const ok =
				file.type.startsWith("video/") ||
				/\.(mp4|mov)$/i.test(file.name);
			if (ok) {
				uploadFile(file, !handled);
				handled = true;
			}
		}
		return handled;
	};

	return { widget: uploadWidget };
};

app.registerExtension({
	name: "ComfyUI-VideoSlice.UploadVideo",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData?.input?.required?.video?.[1]?.video_upload === true) {
			nodeData.input.required.upload_video = ["VIDEOUPLOAD", { widget: "video" }];
		}
	},
});
