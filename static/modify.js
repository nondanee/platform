function unsatisfied(){
	if(confirm("不太满意删了重发?")){
		let xhr=new XMLHttpRequest()
		xhr.onreadystatechange=function()
		{
			if(xhr.readyState==4){
				if(xhr.status==200)
					window.location.href="/"
				else if(xhr.status==403)
					alert("好像已经失去删除权限了。。。")
				else if(xhr.status==404)
					alert("怕是已经删除了呢。。")
				else
					alert("我也不知道发生了什么")
			}
		}
		xhr.open("POST","/delete/"+window.location.href.slice(-6))
		xhr.send()
	}
}
window.onload = function(){
	let title = document.getElementById("title")
	let deleteButton = document.createElement("button")
	deleteButton.id = "delete"
	deleteButton.addEventListener("click",unsatisfied)
	title.parentNode.insertBefore(deleteButton,title)
}