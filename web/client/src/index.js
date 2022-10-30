const version = "0.0.1";
const location = window.location;
const api_url = location.protocol + "//" + location.hostname + ":8000/";

axios.defaults.baseURL = api_url;
axios.defaults.headers["Content-Type"] = "application/json;charset=utf-8;";
axios.defaults.headers.common["Access-Control-Allow-Origin"] = "*"

Chart.defaults.color = '#FFFFFF';
const chartPlugin = {
	id: 'chart_plugin',
	beforeDraw: (chart) => {
		const context = chart.canvas.getContext('2d');
		context.save();
		context.globalCompositeOperation = 'destination-over';
		context.fillStyle = '#454d55';
		context.fillRect(0, 0, chart.width, chart.height);
		context.restore();
	}
}

var charts = {
	dataDistributionsBubbleChart: null,
	gradeDistributionsDoughnutChart: null,
	rankedDensityLineChart: null,
	rankedSpaciousnessLineChart: null,
	rankedPGVLineChart: null
};

const colorScale = d3.interpolateInferno;
const colorRangeInfo = {
	colorStart: 0,
	colorEnd: 1,
	useEndAsStart: false,
};

Vue.component("action-button", {
	props: {title: {type: String}, variant: {type: String}, icon: {type: String}, callback: {type: Function}},
	methods: {
		execute: function(event){
			if (this.callback){
				this.callback(event, this)
			}
		}
	},
	created: function(){
		if (this.variant == null){
			this.variant = "secondary";
		}
	},
	template: "<b-button pill :variant=variant size=\"sm\" v-on:click=\"execute(event)\">"
		+ "{{title}}"
		+ "<b-icon v-if=\"icon\" :icon=icon :varient=variant></b-icon>"
		+ "</b-button>"
});

Vue.component("attribute", {
	props: {name: {type: String}, value: {type: String}, buttontitle: {type: String},
		callback: {type: Function}},
	template: "<b-row align-v=\"center\" class=\"no-gutters attributes\">"
		+ "<b-col class=\"col-auto me-auto\">"
		+ "<div class=\"bg-light text-secondary attribute-name\">{{name}}</div></b-col>"
		+ "<b-col class=\"text-white attribute-value\" v-bind:class=\"{'col-auto me-auto': buttontitle}\"><div>{{value}}</div></b-col>"
		+ "<b-col v-if=\"buttontitle\" class=\"attribute-button\">"
		+ "<action-button v-bind:title=\"buttontitle\" variant=\"outline-light\" :callback=callback></action-button>"
		+ "</b-col></b-row>"
});

new Vue({
	el: "#main-content",
	data: {
		project_list: null,
		project: null,
		algorithm: null,
		form: {
			name: null,
			file: null,
			// encoder: null,
			possible_grades_option: null,
			subspace_param_list_key: null,
			answer_label_dict: {},
			rd_cutoff_adjustment: 0,
			delta_link_threshold_adjustment: 0,
			message: null,
		},
		possible_grades_options: null,
		subspace_param_list_key_options: null,
		answerFields: [
			{key: "index", label: "Rank"},
			{key: "markup", label: "Markup"},
			{key: "id", label: "ID"},
			{key: "text", label: "Text"},
			{key: "assigned_grade", label: "Assigned Grade"}
		],
		answerRepresentationFields: [
			{key: "id", label: "ID"},
			{key: "text", label: "Text"},
		],
		answerNeighbourFields: [
			{key: "id", label: "ID"},
			{key: "text", label: "Text"},
			{key: "assigned_grade", label: "Assigned Grade"},
			{key: "distance", label: "Distance"},
			// {key: "within_rd", label: "Within RD Grade"},
			{key: "density", label: "Density"},
			{key: "spaciousness", label: "Spaciousness"}
		],
		gradingConfirmationFields: [
			{key: "index", label: "Index"},
			{key: "id", label: "ID"},
			{key: "text", label: "Text"},
			{key: "predicted_grade", label: "Predicted Grade"},
			{key: "assigned_grade", label: "Assigned Grade"}
		],
		markupClassOptions: [
			{value: 0, name: "Normal"},
			{value: 1, name: "Class 1"},
			{value: 2, name: "Class 2"},
			{value: 3, name: "Class 3"},
			{value: 4, name: "Class 4"}
		],
		// charts: {
		// 	dataDistributionsBubbleChart: null,
		// 	gradeDistributionsDoughnutChart: null,
		// 	rankedDensityLineChart: null,
		// 	rankedSpaciousnessLineChart: null
		// },
		minDistance: null,
		maxDistance: null,
		minRDAdjustmentValue: null,
		maxRDAdjustmentValue: null,
		minDeltaLinkThresholdAdjustmentValue: null,
		maxDeltaLinkThresholdAdjustmentValue: null,
		localLabels: [],
		gradeDistributionMap: null,
		reducedAnswerMap: null,
		maxRepresentationCount: 0,
		answerNeighbours: null,
		markedCount: 0,
		selectMode: "single",
		currentPage: 1,
		rowPerPage: 10,
		showProjectInfoDetails: true,
		loading: false
	},
	mounted: function(){
		// this.loadData();
	},
	watch: {
		project: {
			handler(newValue, oldValue){
				// setTimeout(this.updateProject, 500);
				if(newValue != null) this.getAlgorithm();
			},
			// deep: true,
			// immediate: true
		},
	},
	methods: {
		saveData: function(projectSaved = false){
			// this.project.saved = projectSaved;
			let localStorage = window.localStorage;
			localStorage.setItem("version", version);
			localStorage.setItem("project", JSON.stringify(this.project));
			// localStorage.setItem("localLabels", JSON.stringify(this.localLabels));
			// localStorage.setItem("answerNeighbours", JSON.stringify(this.answerNeighbours));
		},
		loadData: function(){
			let localStorage = window.localStorage;
			if(localStorage.getItem("version") != version){
				this.deleteData();
				return;
			}
			this.project = JSON.parse(localStorage.getItem("project"));
			// this.project_list = JSON.parse(localStorage.getItem("project_list"));
			// this.localLabels = JSON.parse(localStorage.getItem("localLabels")) || [];
			// this.answerNeighbours = JSON.parse(localStorage.getItem("answerNeighbours"));
			if(this.project == null){
				return;
			}
			this.updateLocalLabels(true);
			this.updateAnswerNeighbours(true);
			this.updateReducedAnswerMap(true);
		},
		deleteData: function(){
			let localStorage = window.localStorage;
			localStorage.removeItem("project");
			localStorage.removeItem("localLabels");
			localStorage.removeItem("answerNeighbours");
		},
		clearForm: function(){
			this.form = {
				name: null,
				file: null,
				encoder: null,
				possible_grades_option: null,
				subspace_param_list_key: null,
				answer_label_dict: {},
				rd_cutoff_adjustment: this.project == null ? 0 : this.project.algorithm.rd_cutoff_adjustment,
				delta_link_threshold_adjustment: this.project == null ? 0 : this.project.delta_link_threshold_adjustment,
				message: null
			}

			// if(this.project != null && (this.minRDAdjustmentValue == null || this.maxRDAdjustmentValue == null)){
			// 	var minRDAdjustmentValue = null;
			// 	var maxRDAdjustmentValue = null;
			// 	this.project.algorithm.reduced_data_distances.map(function(array){
			// 		array.map(function(value){
			// 			if(value > 0 && (minRDAdjustmentValue == null || minRDAdjustmentValue > value)){
			// 				minRDAdjustmentValue = value;
			// 			}
			// 			if(maxRDAdjustmentValue == null || maxRDAdjustmentValue < value){
			// 				maxRDAdjustmentValue = value;
			// 			}
			// 		});
			// 	});
			// 	this.minRDAdjustmentValue = -(this.project.algorithm.rd_cutoff - minRDAdjustmentValue);
			// 	this.maxRDAdjustmentValue = maxRDAdjustmentValue - this.project.algorithm.rd_cutoff;
			// }
		},
		showToast: function(title, message, variant="danger"){
			this.$bvToast.toast(message, {
				title: title,
				autoHideDelay: 3000,
				appendToast: true,
				variant: variant
			});
		},
		updateProjectDetailsMargin: function(){
			var informationPanel = document.getElementById("information-panel");
			var projectDetails = document.getElementById("project-details");
			projectDetails.style.marginTop = informationPanel.offsetHeight + "px";
		},
		expandProjectInfoDetails: function(){
			this.showProjectInfoDetails = !this.showProjectInfoDetails;
			setTimeout(this.drawRankedPGVLineChart);
			setTimeout(this.updateProjectDetailsMargin, 500);
		},
		parseJSONResponse: function(response, callback){
			let reader = new FileReader();
			reader.onload = function(){
				callback(true, JSON.parse(reader.result));
			};
			reader.onerror = function(){
				callback(false, reader.error);
			};
			reader.readAsText(response.data);
		},
		getAlgorithm: function(){
			axios.get("/project/" + this.project.name + "/algorithm/", {
				responseType: "blob"
			}).then(response => {
				this.parseJSONResponse(response, (success, data) => {
					if(success){
						// this.project.algorithm = data;
						// this.$set(this.project, 'algorithm', data);
						this.project.algorithm = data;
						this.getAlgorithmSubspaces();
						// this.$set(this.project.algorithm, 'subspaces', []);
						// setTimeout(this.updateProject, 500);
					} else {
						this.showToast("Error", "Failed to get algorithm");
						this.loading = false;
					}
				});
			}).catch(error => {
				console.log("get_algorithm.error", error);
				this.loading = false;
			});
		},
		getAlgorithmSubspaces: function(page=1){
			axios.get("/project/" + this.project.name + "/algorithm/subspaces/?page=" + page, {
				responseType: "blob"
			}).then(response => {
				this.parseJSONResponse(response, (success, data) => {
					// TO-DO: handle pagination
					if(success){
						// this.$set(this.project.algorithm, 'subspaces', data);
						// setTimeout(this.updateProject, 500);
						if(data.page == 1){
							this.project.algorithm.subspaces = new Array(data.total);
						}
						this.project.algorithm.subspaces[data.page - 1] = data.items[0];
						if(data.page < data.total){
							this.getAlgorithmSubspaces(data.page + 1);
						} else {
							this.$set(this.project.algorithm, 'subspaces', this.project.algorithm.subspaces);
							this.loading = false;
							setTimeout(this.updateProject, 500);
						}
					} else {
						console.log('getAlgorithmSubspaces, fail, page: ' + page);
						this.showToast("Error", "Failed to get subspaces");
						this.loading = false;
					}
				});
			}).catch(error => {
				console.log("get_algorithm_subspaces.error", error);
				this.loading = false;
			});
		},
		updateProject: function(){
			var minDistance = null, maxDistance = null;
			this.project.algorithm.reduced_data_distances.map(function(array){
				array.map(function(value){
					if(value > 0 && (minDistance == null || minDistance > value)){
						minDistance = value;
					}					
					if(maxDistance == null || maxDistance < value){
						maxDistance = value;
					}
				});
			});
			this.minDistance = minDistance;
			this.maxDistance = maxDistance;
			this.form.rd_cutoff_adjustment = this.form.delta_link_threshold_adjustment = 0;
			this.minRDAdjustmentValue = -(this.project.algorithm.rd_cutoff - this.minDistance);
			this.maxRDAdjustmentValue = this.project.algorithm.delta_link_threshold + this.form.delta_link_threshold_adjustment
				- this.project.algorithm.rd_cutoff;
			this.minDeltaLinkThresholdAdjustmentValue = -(this.project.algorithm.delta_link_threshold
				- (this.form.rd_cutoff_adjustment + this.project.algorithm.rd_cutoff))
			this.maxDeltaLinkThresholdAdjustmentValue = this.maxDistance - this.project.algorithm.delta_link_threshold;

			this.updateLocalLabels();
			this.updateAnswerNeighbours();
			this.updateReducedAnswerMap();
			this.$refs.answerTable.refresh();
			this.drawOverviewCharts(true);
			setTimeout(this.updateProjectDetailsMargin, 500);
			if(this.loading){
				this.loading = false;
			}
		},
		getOriginalIndex: function(reducedAnswerIndex){
			for(var i = 0; i < this.project.algorithm.original_to_reduced_index_map.length; i++){
				if(this.project.algorithm.original_to_reduced_index_map[i] == reducedAnswerIndex){
					return i;
				}
			}
			return null;
		},
		updateLocalLabels: function(whenEmpty = false){
			if(this.project == null || this.project.algorithm == null){
				return;
			}
			if(whenEmpty && this.localLabels.length > 0){
				return;
			}
			// update localLabels
			this.gradeDistributionMap = new Map();
			this.project.possible_grades.forEach(grade => {
				this.gradeDistributionMap.set("Marked " + grade, 0);
				this.gradeDistributionMap.set("Predicted " + grade, 0);
			});

			for(var i=0; i<this.project.algorithm.reduced_num_data; i++){
				var key;
				if(i in this.project.algorithm.reduced_known_data_labels){
					this.localLabels[i] = this.project.algorithm.reduced_known_data_labels[i];
					key = "Marked " + this.localLabels[i];
				} else if(this.project.results != null){
					// this.localLabels[i] = this.project.results[this.getOriginalIndex(i)];
					this.localLabels[i] = null;
					key = "Predicted " + this.project.results[this.getOriginalIndex(i)];
				} else {
					this.localLabels[i] = null;
					key = null;
				}
				if(key != null){
					// key += this.localLabels[i];
					this.gradeDistributionMap.set(key, this.gradeDistributionMap.get(key) + 1);
				}
			}
		},
		updateAnswerNeighbours: function(whenEmpty = false){
			if(this.project == null || this.project.algorithm == null){
				return;
			}
			if(whenEmpty && this.answerNeighbours != null){
				return;
			}
			// update answerNeighbours
			this.answerNeighbours = [];
			for(var i=0; i<this.project.algorithm.reduced_num_data; i++){
				var countMap = new Map();
				// for(var s=0; s<this.project.algorithm.subspaces.length; s++){
				this.project.algorithm.subspaces.forEach(subspace => {
					if(subspace.weight <= 0){
						return;
					}
					subspace.nearest_neighbours[i].slice(1, 6).forEach(n => {
						if(countMap.has(n)){
							countMap.set(n, countMap.get(n) + 1);
						} else {
							countMap.set(n, 1);
						}
					});
				});
				this.answerNeighbours[i] = [];
				Array.from(countMap.entries()).sort((a, b) => b[1] - a[1]).slice(0, 5).forEach(item => {
					this.answerNeighbours[i].push(item[0]);
				});
			}
		},
		updateReducedAnswerMap: function(whenEmpty = false){
			if(this.project == null || this.project.algorithm == null){
				return;
			}
			if(whenEmpty && this.reducedAnswerMap != null){
				return;
			}

			this.maxRepresentationCount = 0;
			this.reducedAnswerMap = new Map();
			for(var i=0; i<this.project.algorithm.num_data; i++){
				let reducedIndex = this.project.algorithm.original_to_reduced_index_map[i];
				if(!this.reducedAnswerMap.has(reducedIndex)){
					this.reducedAnswerMap.set(reducedIndex, {
						data: {x: this.project.tsne_data[i][0], y: this.project.tsne_data[i][1], v: 1},
						label: this.project.dataset.answers[i].text,
						representations: [i]
					});
				} else {
					this.reducedAnswerMap.get(reducedIndex).data.v = this.reducedAnswerMap.get(reducedIndex).data.v + 1;
					this.reducedAnswerMap.get(reducedIndex).representations.push(i);
				}
				if(this.maxRepresentationCount < this.reducedAnswerMap.get(reducedIndex).data.v){
					this.maxRepresentationCount = this.reducedAnswerMap.get(reducedIndex).data.v;
				}
			}
		},
		getGradeDistributionString: function(type){
			var string = "";
			if(this.gradeDistributionMap == null){
				return string;
			}
			this.project.possible_grades.forEach((grade, index) => {
				if(index > 0){
					string += ", ";
				}
				string += grade + ": " + this.gradeDistributionMap.get(type + " " + grade);
			});
			return string;
		},
		getAssignedGrade: function(answerIndex, reduced=true){
			if(this.project == null || this.project.dataset == null || this.project.dataset.answers == null){
				return [false, null];
			}
			// if(answerIndex in this.form.answer_label_dict){
			// 	return [true, this.form.answer_label_dict[answerIndex]];
			// } else if(answerIndex in this.project.algorithm.known_data_labels){
			// 	return [false, this.project.algorithm.known_data_labels[answerIndex]];
			// } else {
			// 	return [true, null];
			// }
			var reducedAnswerIndex = reduced ? answerIndex : this.project.algorithm.original_to_reduced_index_map[answerIndex];
			return [!(reducedAnswerIndex in this.project.algorithm.reduced_known_data_labels),
				this.localLabels[reducedAnswerIndex]]
		},
		answerTableRowClass: function(item, type){
			// if(this.project.dataset.answers[this.getOriginalIndex(item)].markup){
			// 	return "table-success";
			// }
			switch(this.project.dataset.answers[this.getOriginalIndex(item)].markup_class){
				case 1: return "table-success"; break;
				case 2: return "table-warning"; break;
				case 3: return "table-info"; break;
				case 4: return "table-danger"; break;
				default: return;
			}
		},
		answerGradeChanged: function(reducedAnswerIndex, value){
			let originalAnswerIndex = this.getOriginalIndex(reducedAnswerIndex);
			if(value == null && originalAnswerIndex in this.form.answer_label_dict){
				delete this.form.answer_label_dict[originalAnswerIndex]
			} else if(value != null){
				this.form.answer_label_dict[originalAnswerIndex] = value;
			}
			this.markedCount = Object.keys(this.form.answer_label_dict).length;
		},
		markupChanged: function(reducedAnswerIndex, value){
			// this.project.dataset.answers[this.getOriginalIndex(reducedAnswerIndex)].markup = value;
			this.answerMarkup(reducedAnswerIndex, value);
			// this.saveData(false);
		},
		clearSelection: function(){
			this.$refs.answerTable.clearSelected();
		},
		answerSelected: function(selectedItems){
			if(selectedItems.length == 0){
				return;
			}
			this.project.selected_answer_index = selectedItems[0];
			this.$bvModal.show("modal-answer-details");
		},
		calculatePoint: function(i, intervalSize, colorRangeInfo) {
			var { colorStart, colorEnd, useEndAsStart } = colorRangeInfo;
			return (useEndAsStart ? (colorEnd - (i * intervalSize)) : (colorStart + (i * intervalSize)));
		},
		interpolateColors: function(dataLength, colorScale, colorRangeInfo){
			var { colorStart, colorEnd } = colorRangeInfo;
			var colorRange = colorEnd - colorStart;
			var intervalSize = colorRange / dataLength;
			var i, colorPoint;
			var colorArray = [];

			for (i = 0; i < dataLength; i++) {
				colorPoint = this.calculatePoint(i, intervalSize, colorRangeInfo);
				colorArray.push(colorScale(colorPoint));
			}

			return colorArray;
		},
		drawChart: function(chart, element, type, title, xTitle, yTitle, legend, data, labelCallback, extraOptions,
			redraw = false){
			if(!redraw && chart != null){
				return chart;
			// } else if(redraw && chart != null){
			// 	console.log("data.datasets", data.datasets);
			// 	// chart.destroy();
			// 	// remove data
			// 	chart.data.labels = [];
			// 	chart.data.datasets = [];

			// 	// add data
			// 	if(data.labels != null){
			// 		data.labels.forEach(labels => {
			// 			chart.data.labels.push(labels);
			// 		});
			// 	}
			// 	data.datasets.forEach(dataset => {
			// 		chart.data.datasets.push(dataset);
			// 	});
			// 	chart.update();
			// 	return chart;
			// }
			} else if(chart != null){
				chart.destroy();
			}

			let options = {
				responsive: true,
				plugins: {
					legend: legend,
					title: {display: true, text: title},
					tooltip: {callbacks: {label: labelCallback}},
				}
			};

			if(type != 'doughnut'){
				options.scales = {
					x: {
						grid: {drawBorder: false, color: '#8f8c92'},
						title: {display: true, text: xTitle}
					},
					y: {
						grid: {drawBorder: false, color: '#8f8c92'},
						title: {display: true, text: yTitle}
					},
				};
			} else {
				options.layout = {padding: {bottom: 10}};
			}

			if(extraOptions != null){
				for(const [key, value] of Object.entries(extraOptions)){
					if(key in options){
						options[key] = Object.assign({}, value, options[key]);
					} else {
						options[key] = value;
					}
				};
			}
			chart = new Chart(element.getContext('2d'), {
				type: type,
				data: data,
				plugins: [chartPlugin],
				options: options
			});
			return chart;
		},
		drawDataDistributionsBubbleChart: function(redraw = false){
			// let colors = this.interpolateColors(this.project.possible_grades.length + 1, colorScale,
			// 	colorRangeInfo).slice(1);
			let possibleGrades = [];
			this.project.possible_grades.forEach((grade, index) => {
				possibleGrades.splice(index, 0, "Marked " + grade);
				possibleGrades.push("Predicted " + grade);
			});
			let colors = this.interpolateColors(possibleGrades.length + 1, colorScale,
				colorRangeInfo).slice(1);
			// let data = [], dataLabels = [], labels = [], backgroundColors = [];
			// this.reducedAnswerMap.forEach((value, key) => {
			// 	data.push(value.data);
			// 	dataLabels.push(value.label);
			// 	labels.push(this.localLabels[key]);
			// 	let gradeIndex = this.project.possible_grades.indexOf(this.localLabels[key]);
			// 	backgroundColors.push(gradeIndex == -1 ? colors[0] : colors[gradeIndex]);
			// });
			let datasets = new Map();
			this.reducedAnswerMap.forEach((value, key) => {
				// let label = this.localLabels[key] == null ? "Unknown" : this.localLabels[key];
				let originalIndex = this.getOriginalIndex(key);
				let label = this.project.results == null ? "Unknown" : ((this.localLabels[key] == null ? "Predicted " : "Marked ") + this.project.results[originalIndex]);
				let labelIndex = Math.max(0, possibleGrades.indexOf(label));
				var mapValue;
				if(!datasets.has(label)){
					mapValue = {
						label: label,
						data: [], dataLabels: [],
						borderColor: "rgba(255, 255, 255, 0.4)",
						backgroundColor: colors[labelIndex]
					};
				} else {
					mapValue = datasets.get(label);
				}
				mapValue.data.push(value.data);
				mapValue.dataLabels.push(value.label);
				datasets.set(label, mapValue);
			});
			let maxRepresentationCount = this.maxRepresentationCount;

			let d = [];
			if(this.project.results != null){
				possibleGrades.forEach(grade => {
					// d.push(datasets.get(grade));
					if(datasets.has(grade)){
						d.push(datasets.get(grade))
					}
				});
			} else {
				d.push(datasets.get("Unknown"));
			}

			// let colors = this.interpolateColors(data.length, colorScale, colorRangeInfo);
			let chartData = {
				// datasets: [{
				// 	label: labels,
				// 	data: data,
				// 	dataLabels: dataLabels,
				// 	borderColor: "rgba(255, 255, 255, 0.5)",
				// 	backgroundColor: backgroundColors
				// }]
				// datasets: Array.from(datasets.values())
				datasets: d
			};
			let extraOptions = {
				elements: {
					point: {
						radius: function(context){
							return context.raw.v * 20 / maxRepresentationCount;
						}
					}
				}
			};
			charts.dataDistributionsBubbleChart = this.drawChart(charts.dataDistributionsBubbleChart,
				this.$refs.dataDistributionsBubbleChart, "bubble", "Data Distributions In 2-D View",
				"X", "Y", true, chartData,
				function(context){
					return context.dataset.dataLabels[context.dataIndex]
						+ " (" + context.dataset.data[context.dataIndex].v + ")";
				}, extraOptions, redraw);
		},
		drawGradeDistributionsDoughnutChart: function(redraw = false){
			var labels = null, data = null;

			if(this.project.results == null){
				labels = ["Unknown"];
				data = [this.localLabels.length];
			} else {
				let markedLabels = [], predictedLabels = [];
				this.project.possible_grades.forEach(grade => {
					markedLabels.push("Marked " + grade);
					predictedLabels.push("Predicted " + grade);
				});
				labels = markedLabels.concat(predictedLabels);
				data = new Array(labels.length).fill(0);
				for(var i=0; i<this.localLabels.length; i++){
					var label = "";
					if(i in this.project.algorithm.reduced_known_data_labels){
						label = "Marked " + this.localLabels[i];
					} else {
						label = "Predicted " + this.project.results[this.getOriginalIndex(i)];
					}
					data[labels.indexOf(label)] += 1;
				}
			}
			let colors = this.interpolateColors(labels.length + 1, colorScale, colorRangeInfo).slice(1);
			
			let chartData = {
				labels: labels,
				datasets: [{
					data: data,
					borderColor: colors,
					backgroundColor: colors
				}]
			};
			charts.gradeDistributionsDoughnutChart = this.drawChart(charts.gradeDistributionsDoughnutChart,
				this.$refs.gradeDistributionsDoughnutChart, "doughnut", "Grade Distributions",
				"X", "Y", true, chartData,
				function(context){
					// return labels[context.dataIndex];
					return labels[context.dataIndex] + " (" + data[context.dataIndex] + ")"
				}, {}, redraw);
		},
		drawRankedLineChart: function(chart, element, sourceArray, title, yTitle, drawSelected = false,
			annotationTypes = null, reverse = false, redraw = false){
			let selectedIndex = this.project.selected_answer_index;
			let rankedValues = [];
			for(var i=0; i<sourceArray.length; i++){
				rankedValues.push({
					value: sourceArray[i],
					index: i,
					label: this.project.dataset.answers[this.getOriginalIndex(i)].text
				});
			}
			rankedValues.sort(function(a, b){
				if(!reverse){
					return (a.value < b.value ? -1 : ((a.value == b.value) ? 0 : 1));
				} else {
					return (a.value < b.value ? 1 : ((a.value == b.value) ? 0 : -1));
				}
			});
			
			let rangeColors = this.interpolateColors(drawSelected ? 3: sourceArray.length, colorScale, colorRangeInfo);			
			let ranks = [], data = [], dataLabels = [], colors = [];
			rankedValues.forEach((item, rank) => {
				if(drawSelected && item.index != selectedIndex && this.answerNeighbours[selectedIndex].indexOf(item.index) == -1){
					return;
				}
				ranks.push(rank);
				data.push(item.value);
				dataLabels.push(item.label);
				if(drawSelected){
					if(item.index == selectedIndex){
						colors.push("#8fd19e");
					} else if(this.project.algorithm.reduced_data_distances[selectedIndex][item.index] <= this.project.algorithm.rd_cutoff){
						colors.push(rangeColors[2]);
					} else {
						colors.push(rangeColors[1]);
					}
				} else {
					colors.push(rangeColors[rank]);
				}
			});
			
			let chartData = {
				labels: ranks,
				datasets: [{
					type: 'line',
					data: data,
					dataLabels: dataLabels,
					borderColor: "rgba(255, 255, 255, 0.2)",
					backgroundColor: colors,
					pointRadius: 5,
					tension: 0.1
				}],
			};
			var extraOptions = null;
			if(annotationTypes != null){
				let annotations = [];
				annotationTypes.forEach(type => {
					var borderColor, label, value;
					if(type == "rd_cutoff" || type == "pgv"){
						borderColor = "#8fd19e";
						if(type == "rd_cutoff"){
							value = this.project.algorithm.rd_cutoff;
							label = "MASD - " + value.toFixed(4);
						} else if(this.localLabels[this.project.ordered_answer_list[0]] == null){
							// value = this.project.pgv_values[this.project.ordered_answer_list[0]];
							value = Object.keys(this.project.algorithm.reduced_known_data_labels).length;
							label = "Next Suggested Answer";
						}
					} else {
						borderColor = "#b56576";
						value = this.project.algorithm.delta_link_threshold;
						label = "RTAD - " + value.toFixed(4);
					}

					var annotation = {
						type: "line",
						borderColor: borderColor,
		  				borderWidth: 3,
		  				label: {
		    				enabled: true,
		    				font: { size: 10 },
		    				borderColor: borderColor,
		    				backgroundColor: "rgba(0, 0, 0, 0.3)",
		    				borderRadius: 10,
		    				borderWidth: 2,
		    				content: (ctx) => label,
		    				// rotation: "auto"
		  				},
		  				scaleID: type == "pgv" ? "x" : "y",
		  				value: value
					};
					annotations.push(annotation);
				});
				extraOptions = {
					plugins: { annotation: { annotations: annotations } }
				}
			}
			return this.drawChart(chart, element, "line", title, "Rank", yTitle, null, chartData,
				function(context){
					return context.dataset.dataLabels[context.dataIndex];
				}, extraOptions, redraw);
		},
		drawRankedPGVLineChart: function(){
			let pgvValues = [];
			var markedCount = 0, maxValue = null;
			this.project.pgv_values.forEach((value, index) => {
				if(!(index in this.project.algorithm.reduced_known_data_labels)){
					pgvValues.push(value);
				} else {
					markedCount += 1;
				}
				if(maxValue == null || maxValue < value){
					maxValue = value;
				}
			});
			pgvValues = new Array(markedCount).fill(maxValue).concat(pgvValues);
			if(this.showProjectInfoDetails){
				charts.rankedPGVLineChart = this.drawRankedLineChart(
					charts.rankedPGVLineChart, this.$refs.rankedPGVLineChart, pgvValues,
					"Perceived Grading Rank (PGR)", "Perceived Grading Value (PGV)", false, ["pgv"],
					true, true);
			} else if(charts.rankedPGVLineChart != null){
				charts.rankedPGVLineChart.destroy();
				charts.rankedPGVLineChart = null;
			}
		},
		drawOverviewCharts: function(redraw = false){
			if(this.project == null || this.project.algorithm == null){
				return;
			}
			this.drawDataDistributionsBubbleChart(redraw);
			this.drawGradeDistributionsDoughnutChart(redraw);
			charts.rankedDensityLineChart = this.drawRankedLineChart(
				charts.rankedDensityLineChart, this.$refs.rankedDensityLineChart,
				this.project.algorithm.densities, "Ranked Densities of Encapsulated Data",
				"Normalized Density", false, null, false, redraw);
			// charts.rankedSpaciousnessLineChart = this.drawRankedLineChart(
			// 	charts.rankedSpaciousnessLineChart,
			// 	this.$refs.rankedSpaciousnessLineChart, this.project.algorithm.spaciousness,
			// 	"Ranked Spaciousness of Encapsulated Data", "Normalized Spaciousness", false, [], redraw);
			charts.rankedSpaciousnessLineChart = this.drawRankedLineChart(
				charts.rankedSpaciousnessLineChart, this.$refs.rankedSpaciousnessLineChart,
				this.project.algorithm.averaged_spaciousness,
				"Ranked Spaciousness of Encapsulated Data", "Averaged Spaciousness", false,
				["rd_cutoff", "delta_link_threshold"], false, redraw);
			this.drawRankedPGVLineChart();
		},
		drawAnswerCharts: function(){
			let selectedIndex = this.project.selected_answer_index;
			let originalSelectedIndex = this.getOriginalIndex(selectedIndex);
			let selected_data = this.project.tsne_data[originalSelectedIndex];
			// let neighbours = [], neighboursText = [];
			let neighboursWithinRD = [], neighboursBeyondRD = [];
			let neighboursWithinRDText = [], neighboursBeyondRDText = [];
			this.answerNeighbours[this.project.selected_answer_index].forEach(n => {
				var index = this.getOriginalIndex(n);
				// neighbours.push({x: this.project.tsne_data[index][0], y: this.project.tsne_data[index][1]});
				// neighboursText.push(this.project.dataset.answers[index].text);
				let data = {x: this.project.tsne_data[index][0], y: this.project.tsne_data[index][1]};
				let text = this.project.dataset.answers[index].text;
				if(this.project.algorithm.reduced_data_distances[selectedIndex][n] <= this.project.algorithm.rd_cutoff){
					neighboursWithinRD.push(data);
					neighboursWithinRDText.push(text);
				} else {
					neighboursBeyondRD.push(data);
					neighboursBeyondRDText.push(text);
				}
			});
			let colors = this.interpolateColors(3, colorScale, colorRangeInfo);
			let chartData = {
				datasets: [{
					label: "Selected",
					data: [{x: selected_data[0], y: selected_data[1]}],
					dataLabels: [this.project.dataset.answers[originalSelectedIndex].text],
					// borderColor: '#95999c',
					borderColor: "rgba(255, 255, 255, 0.3)",
					backgroundColor: '#8fd19e',
					pointRadius: 10,
				}, {
					// label: 'Neighbours Within RD',
					label: 'Semantically Equivalent Answers',
					data: neighboursWithinRD,
					dataLabels: neighboursWithinRDText,
					// borderColor: '#89231d',
					// backgroundColor: '#b56576',
					borderColor: "rgba(255, 255, 255, 0.3)",
					backgroundColor: colors[2],
					pointRadius: 10
				}, {
					// label: "Neighbours Beyond RD",
					label: 'Marginal',
					data: neighboursBeyondRD,
					dataLabels: neighboursBeyondRDText,
					borderColor: "rgba(255, 255, 255, 0.3)",
					backgroundColor: colors[1],
					pointRadius: 10
				}]
			};
			this.drawChart(null, this.$refs.answerDistanceChart, "scatter",
				"Distance To Neighbours In 2-D View", "X", "Y", true, chartData,
				function(context){
					return context.dataset.dataLabels[context.dataIndex];
				}, {}, false);
			this.drawRankedLineChart(null, this.$refs.answerRankedDensityLineChart,
				this.project.algorithm.densities, "Ranked Densities Among Neighbours",
				"Normalized Density", true, null, false, false);
			this.drawRankedLineChart(null, this.$refs.answerRankedSpaciousnessLineChart,
				this.project.algorithm.spaciousness, "Ranked Spaciousness Among Neighbours",
				"Normalized Spaciousness", true, null, false, false);
		},
		createProject: function(event){
			if(this.loading){
				return;
			}
			if(!this.$refs.createProjectForm.checkValidity()){
				this.form.message = "All Fields are required!";
				event.preventDefault();
				return;
			} else {
				this.form.name = this.form.name.trim();
				if(!(new RegExp("^[a-zA-Z0-9._ ]*$")).test(this.form.name)){
					this.form.message = "Special Characters (except dot and underscore) are not allowed in Name";
					event.preventDefault();
					return;
				}
			}

			this.form.message = null;
			this.loading = true;

			var formData = new FormData();
			formData.append("name", this.form.name);
			formData.append("file", this.form.file);
			// formData.append("encoder", this.form.encoder);
			formData.append("possible_grades_option", this.form.possible_grades_option);
			formData.append("subspace_param_list_key", this.form.subspace_param_list_key);
			axios.post("/project/create/", formData, {
				headers: {"Content-Type": "multipart/form-data"},
				responseType: "blob"
			}).then(response => {
				// this.project = response.data;
				// this.updateLocalLabels();
				// this.updateAnswerNeighbours();
				// this.updateReducedAnswerMap();
				// if(this.project_list == null){
				// 	this.project_list = [];
				// }
				// this.project_list.push(this.project.name);
				// this.loading = false;
				// this.$bvModal.hide("modal-create-project");

				this.parseJSONResponse(response, (success, data) => {
					if(success){
						this.project = data;
						// this.updateLocalLabels();
						// this.updateAnswerNeighbours();
						// this.updateReducedAnswerMap();

						// this.$refs.answerTable.refresh();
						// this.drawOverviewCharts(true);
						if(this.project_list == null){
							this.project_list = [];
						}
						this.project_list.push(this.project.name);
					} else {
						this.showToast("Error", "Failed to create project");
						this.loading = false;
					}
					// this.loading = false;
					this.$bvModal.hide("modal-create-project");
				});
			}).catch(error => {
				console.log("create_project, error", error);
				this.loading = false;
				// this.$bvModal.hide("modal-create-project");
				var title, message;
				if(error.response != null && error.response.status == 409){
					title = "Duplicated Project Name";
					message = "Please try a different name or \"Load Project\"";
				} else if(error.response != null && error.response.data != null){
					title = "Error";
					message = error.response.data.detail;
				} else {
					title = "Error";
					message = "Internal Server Error";
				}
				this.showToast(title, message);
			});
		},
		getProjectOptions: function(event){
			if(this.loading){
				return;
			}

			if(this.possible_grades_options != null && this.subspace_param_list_key_options != null){
				this.$bvModal.show("modal-create-project");
				return;
			}

			this.loading = true;
			axios.get("/project/options/", {
			}).then(response => {
				this.possible_grades_options = [];
				for(let [key, value] of Object.entries(response.data.possible_grades_options)){
					this.possible_grades_options.push({key: key, value: value});
				}
				this.subspace_param_list_key_options = response.data.subspace_option_list;
				this.loading = false;
				this.getProjectOptions(event);
			}).catch(error => {
				console.log("getProjectOptions, error", error);
				this.loading = false;
			});
		},
		getProjectList: function(event, callback_type = 'load'){
			if(this.loading){
				return;
			}

			if(this.project_list != null){
				if(this.project_list.length > 0){
					// this.$bvModal.show("modal-load-project");
					this.$bvModal.show("modal-" + callback_type + "-project");
				} else {
					this.showToast("No project Available", "Start by creating a project");
				}
				return;
			}

			this.loading = true;
			axios.get("/project/list/", {
			}).then(response => {
				this.project_list = response.data.project_list;
				this.loading = false;
				this.getProjectList(event, callback_type);
			}).catch(error => {
				console.log("getProjectList, error", error);
				this.loading = false;
			});
		},
		loadProject: function(event){
			if(this.loading){
				return;
			}

			if(!this.$refs.loadProjectForm.checkValidity()){
				this.form.message = "Project name is required!";
				event.preventDefault();
				return;
			}

			this.form.message = null;
			this.loading = true;

			axios.post("/project/load/?name=" + this.form.name, {}, {
				responseType: "blob"
			}).then(response => {
				this.parseJSONResponse(response, (success, data) => {
					if(success){
						this.project = data;
						// this.updateLocalLabels();
						// this.updateAnswerNeighbours();
						// this.updateReducedAnswerMap();

					} else {
						this.showToast("Error", "Failed to load project");
						this.loading = false;
					}
					// this.loading = false;
				});
			}).catch(error => {
				console.log("load_project.error", error);
				this.loading = false;
			});
		},
		saveProject: function(event){
			if(this.loading){
				return;
			}
			this.loading = true;
			axios.post("/project/" + this.project.name + "/save/", {
			}).then(response => {
				this.loading = false;
				// this.saveData(true);
			}).catch(error => {
				console.log("save_project, error", error);
				this.loading = false;
			})
		},
		deleteProject: function(event){
			if(this.loading){
				return;
			}

			if(!this.$refs.deleteProjectForm.checkValidity()){
				this.form.message = "Project name is required!";
				event.preventDefault();
				return;
			}

			this.form.message = null;
			this.loading = true;

			axios.post("/project/" + this.form.name + "/delete/", {				
			}).then(response => {
				this.project_list.splice(this.project_list.indexOf(this.form.name), 1);
				if(this.project != null && this.form.name == this.project.name){
					this.project = null;
					this.deleteData();
				}
				this.loading = false;
			}).catch(error => {
				console.log("delete_project, error", error);
				this.loading = false;
			});
		},
		answerMarkup: function(reducedAnswerIndex, value){
			if(this.loading){
				return;
			}
			// this.loading = true;

			let formData = new FormData();
			formData.append("original_index", this.getOriginalIndex(reducedAnswerIndex));
			formData.append("value", value);
			axios.post("/project/" + this.project.name + "/markup/", formData, {
				headers: {"Content-Type": "multipart/form-data"},
			}).then(response => {
				this.project.dataset.answers[response.data.index].markup = response.data.markup;
				// this.$refs.answerTable.refresh();
				// this.loading = false;
			}).catch(error => {
				console.log("answerMarkup, error", error);
				// this.loading = false;
			});
		},
		addData: function(event){
			if(this.loading){
				return;
			}
			if(!this.$refs.addDataForm.checkValidity()){
				this.form.message = "File is required!";
				event.preventDefault();
				return;
			}

			this.form.message = null;
			this.loading = true;

			let formData = new FormData();
			formData.append("file", this.form.file);
			axios.post("/project/" + this.project.name + "/adddata/", formData, {
				headers: {"Content-Type": "multipart/form-data"},
				responseType: "blob"
			}).then(response => {
				// this.project = response.data;
				// this.loading = false;
				this.parseJSONResponse(response, (success, data) => {
					if(success){
						this.project = data;
						// this.updateLocalLabels();
						// this.updateAnswerNeighbours();
						// this.updateReducedAnswerMap();
						// this.$refs.answerTable.refresh();
						// this.drawOverviewCharts(true);
					} else {
						this.project = null;
						this.showToast("Error", "Failed to add data");
					}
					this.loading = false;
				});
			}).catch(error => {
				console.log('add_data, error', error);
				this.loading = false;
			});
		},
		adjustCutoff: function(adjust_type){
			if(this.loading){
				return;
			}
			this.loading = true;
			var formData = new FormData();
			formData.append("adjust_type", adjust_type);
			formData.append("value", this.form.rd_cutoff_adjustment);
			axios.post("/project/" + this.project.name + "/algorithm/adjust/", formData, {
				headers: {"Content-Type": "multipart/form-data"},
				responseType: "blob"
			}).then(response => {
				// this.project = response.data;
				// this.updateLocalLabels();
				// // this.saveData(false);
				// this.loading = false;

				this.parseJSONResponse(response, (success, data) => {
					if(success){
						this.project = data;
						this.updateLocalLabels();
						this.loading = false;
					} else {
						this.project = null;
						this.showToast("Error", "Failed to adjust RD");
					}
					this.loading = false;
				});
			}).catch(error => {
				console.log('adjustRD, error', error);
				this.loading = false;
			});
		},
		// getAlgorithm: function(event){
		// 	if(this.loading){
		// 		return;
		// 	}
		// 	this.loading = true;
		// 	console.log("get_algorithm");
		// 	axios.get("/project/" + this.project.name + "/algorithm/", {
		// 		validateStatus: function(status){
		// 			return status >= 200 && status < 300;
		// 		}
		// 	}).then(response => {
		// 		console.log("get_algorithm.response", response);
		// 		this.project.algorithm = response.data;
		// 		this.loading = false;
		// 	}).catch(error => {
		// 		console.log("get_algorithm.error", error);
		// 		this.loading = false;
		// 	})
		// },
		markAnswers: function(event){
			if(this.markedCount <= 0){
				this.showToast("No Answer Marked", "Please mark at least 1 answer to run");
				return;
			} else if (!this.$refs.gradingConfirmationModal.isShow){
				this.$bvModal.show('modal-grading-confirmation');
				return;
			} else {
				this.$bvModal.hide('modal-grading-confirmation');
			}
			if(this.loading){
				return;
			}
			this.loading = true;
			axios.post("/project/" + this.project.name + "/mark_answers/", this.form.answer_label_dict, {
			}).then(response => {
				this.project.algorithm.known_data_labels = response.data.algorithm.known_data_labels;
				this.project.algorithm.reduced_known_data_labels = response.data.algorithm.reduced_known_data_labels;
				this.project.ordered_answer_list = response.data.ordered_answer_list;
				this.project.results = response.data.results;
				this.form.answer_label_dict = {};
				this.markedCount = 0;
				// this.$root.$emit("bv::refresh::answerTable", "answer-table");
				this.updateLocalLabels();
				this.currentPage = 1;
				this.$refs.answerTable.refresh();
				this.drawDataDistributionsBubbleChart(true);
				this.drawGradeDistributionsDoughnutChart(true);
				this.drawRankedPGVLineChart(true);
				this.loading = false;
				// this.saveData(false);
			}).catch(error => {
				console.log("markAnswers, error", error);
				this.loading = false;
				this.showToast("Failed to mark answers");
			});
		},
		exportResult: function(event, element, fileType = "csv"){
			if(!this.project || !this.project.results){
				return;
			}
			let headers = ["Project Name", "Possible Grades", "Subspaces", "Answer ID", "Answer Text",
				"Assigned Grade", "Manually Marked"]
			let rows = []
			for(var i=0; i<this.project.algorithm.num_data; i++){
				let answer = this.project.dataset.answers[i];
				let reducedIndex = this.project.algorithm.original_to_reduced_index_map[i];
				rows.push([this.project.name, "\"" + String(this.project.possible_grades) + "\"",
					this.project.subspace_param_list_key, answer.id,
					'"' + answer.text + '"', this.project.results[i],
					reducedIndex in this.project.algorithm.reduced_known_data_labels]);
			}

			var values;
			if(fileType == "csv"){
				values = String(headers) + '\n';
				rows.forEach(row => {
					// row.forEach(value => {
					// 	if((typeof value) == "string" && value.search(/("|,|\n)/g) >= 0){
					// 		value = '"' + value + '"';
					// 	}
					// });
					values += String(row) + '\n';
				});
			}

			let fileName = this.project.name.replace(" ", "_") + "_result." + fileType;
			let blob = new Blob([values], {type: 'text/csv;charset=utf-8;'});
			if(navigator.msSaveBlob){				
				navigator.msSaveBlob(blob, fileName);	//	for IE 10+
			} else {
				let link = document.createElement("a");
				link.setAttribute("href", URL.createObjectURL(blob));
				link.setAttribute("download", fileName);
				link.style.visibility = "hidden";
				document.body.appendChild(link);
				link.click();
				document.body.removeChild(link);
			}
		}
	}
});