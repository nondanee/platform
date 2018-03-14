const titleInput = document.getElementById("title")
const subtitleInput = document.getElementById("subtitle")
const providerInput = document.getElementById("provider")
const typeSelect = document.getElementById("type")
const articleInput = document.getElementById("article")
const photoInput = document.getElementById("photo")
const submitButton = document.getElementById("submit")
const editorForm = document.getElementById("editor")
const photoGallery = document.getElementById("done")

photoInput.addEventListener("change", function () { 

	if(this.files[0])
	{
		let file_name = this.files[0].name
		file_name = file_name.split(".")
		let extend_name = file_name.pop().toUpperCase()
		if (extend_name != "PNG" && extend_name != "GIF" && extend_name != "JPG" && extend_name != "JPEG"){
			showMessage("UNSUPPORTED FILE TYPE",2000)
			this.parentNode.reset()
			return
		}

		let size = this.files[0].size
		if (size/1048576 > 3){
			showMessage("IMAGE IS TOO LARGE",2000)
			this.parentNode.reset()
			return
		}

		let formData = new FormData()
		formData.append("file", this.files[0])
		let backgroundImage = window.URL.createObjectURL(this.files[0])
		this.parentNode.reset()

		let xhr = new XMLHttpRequest()
		xhr.onreadystatechange = function()
		{
			if(xhr.readyState == 4){
				if(xhr.status == 200){
					let url_name = xhr.responseText

					let block = document.createElement('div')
					block.className = "uploaded"
					block.value = url_name
					block.style.backgroundImage = "url(" + backgroundImage + ")"
					let tips = document.createElement('div')
					tips.className = "tips"
					tips.setAttribute("index",photoGallery.childNodes.length+1)
					let deleteButton = document.createElement('button')
					deleteButton.className = "delete"

					block.appendChild(deleteButton)
					block.appendChild(tips)
					photoGallery.appendChild(block)

					tips.onclick = function(){
						let index = [].indexOf.call(photoGallery.childNodes,this.parentNode) + 1
						addToArticle(index,url_name)
					}

					deleteButton.onclick =  function (){
						photoGallery.removeChild(this.parentNode)
						deletePhoto(url_name)
						refreshIndex()
					}

					photoGallery.scrollTop = photoGallery.scrollHeight

				}
				else if(xhr.status == 413)
					showMessage("IMAGE IS TOO LARGE",2000)
				else if(xhr.status == 415)
					showMessage("UNSUPPORTED FILE TYPE",2000)
				else if(xhr.status == 406)
					showMessage("DUPLICATE UPLOADING IMAGE",2000)
				else
					showMessage("UNKNOWN ERROR",2000)
			}
		}
		xhr.open("POST","/upload/photo?token="+token)
		xhr.send(formData)		
	}
})


function addToArticle(index,url_name) {

	let image = '!['+index+']('+url_name+')'

	let value = articleInput.value
	let selectStart = articleInput.selectionStart
	let selectEnd = articleInput.selectionEnd

	if (selectStart==value.length&&selectEnd==value.length){

		if (value.length==0||value[value.length-1]=='\n'){
			articleInput.value = value + image
		}
		else{
			articleInput.value = value + '\n' + image + '\n'
		}

	}
	else{
		articleInput.value = value.substring(0,selectStart) + image + value.substring(selectEnd,value.length)
		articleInput.setSelectionRange(selectStart,selectEnd)
	}

	autoExtend(articleInput,480)
	checkStatus()

}


function autoExtend(element,height){
	let before = document.body.scrollTop
	element.style.height = height+'px'
	element.style.height = (element.scrollHeight)+'px'
	document.body.scrollTop = before
}
articleInput.addEventListener("input", function () { 
	autoExtend(this,480)
})
titleInput.addEventListener("input", function () {
	autoExtend(this,58)
})
function checkStatus(){
	if (titleInput.value==""||subtitleInput.value==""||providerInput.value==""||articleInput.value=="")
		submitButton.disabled = true
	else
		submitButton.disabled = false
}
editorForm.addEventListener("input",checkStatus)




function deletePhoto(url_name){
	let regexp = new RegExp("\\!\\[[^\\]]*\\]\\(" + url_name + "\\)\n{0,1}","g")
	let value = articleInput.value
	articleInput.value = value.replace(regexp,"")
}
function refreshIndex(){
	let photos = photoGallery.childNodes
	let value = articleInput.value
	for(let x=0;x<photos.length;x++){
		
		photos[x].childNodes[1].setAttribute("index",x+1)
		let url_name = photos[x].value
		let image = "!["+(x+1)+"]("+url_name+")"

		let regexp = new RegExp("\\!\\[[^\\]]*\\]\\(" + url_name + "\\)","g")
		value = value.replace(regexp,image)
	}
	articleInput.value = value
}

submitButton.onclick = function (){
	showConfirm()
}

function submitArticle(){
	
	let title = titleInput.value
	let subtitle = subtitleInput.value
	let provider = providerInput.value
	let type = typeSelect.value
	let article = articleInput.value

	let postData = "title="+title+"&subtitle="+subtitle+"&provider="+provider+"&type="+type+"&article="+article

	let xhr=new XMLHttpRequest()
	xhr.onreadystatechange=function()
	{
		if(xhr.readyState==4){
			if(xhr.status==200)
				congraduation(xhr.responseText)
			else 
				showMessage("UNKNOWN ERROR",2000)
		}
	}
	xhr.open("POST","/upload/article?token="+token)
	xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
	xhr.send(postData)
}


function showMessage(message,timeOut){
	const messageBox = document.getElementById("message")
	messageBox.innerHTML = message
	messageBox.className = "show"
	setTimeout(function() {
		messageBox.className = "hidden"
	}, timeOut);
}

function showConfirm(){

	let cover = document.createElement('div')
	cover.className = "cover"
	let confirm = document.createElement('div')
	confirm.className = "confirm"
	let check = document.createElement('button')
	check.className = "check"
	let cancal = document.createElement('button')
	cancal.className = "cancal"

	confirm.appendChild(check)
	confirm.appendChild(cancal)
	cover.appendChild(confirm)
	document.body.appendChild(cover)

	cover.onclick = function(){
		cover.parentNode.removeChild(cover)
	}

	cancal.onclick = function(event){
		event.stopPropagation()
		cover.parentNode.removeChild(cover)
	}

	confirm.onclick = function(){
		event.stopPropagation()
		cover.parentNode.removeChild(cover)
		submitArticle()
	}
}

function congraduation(view_path){
	let cover = document.createElement('div')
	cover.className = "cover"
	let thanks = document.createElement('div')
	thanks.className = "thanks"
	cover.appendChild(thanks)
	document.body.appendChild(cover)
	thanks.addEventListener("webkitAnimationEnd",function() {
		window.location.href = view_path
	})
}

