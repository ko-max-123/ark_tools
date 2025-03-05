const { ipcRenderer } = require('electron');
const fs = require('fs');
const path = require('path');
document.addEventListener('DOMContentLoaded', () => {
    fetch('assets/json/items.json')
        .then(response => response.json())
        .then(data => {
            // HTMLに表示する
            const content = document.getElementById('content');

            data.forEach(item => {
                // itemIdが数字のみで、groupIDがexpではないアイテムを抽出
                if (/^\d+$/.test(item.itemId) &&
                    item.groupID !== 'exp' &&
                    item.groupID !== 'skillbook' &&
                    item.groupID !== 'chip' &&
                    item.groupID !== 'carbon' &&
                    item.groupID !== 'other'
                ) {
                    const itemDiv = document.createElement('div');
                    itemDiv.classList.add('card');
                    itemDiv.classList.add('mb-4');
                    itemDiv.classList.add('rounded-3');
                    itemDiv.classList.add('shadow-sm');
                    itemDiv.style.width = '20%';
                    itemDiv.style.cursor = 'pointer';
                    itemDiv.addEventListener('click', () => {
                        ipcRenderer.send('open-item_detail-window', item.itemId);
                    });
                    console.log("item.itemId", item.itemId);

                    itemDiv.innerHTML = `
                        <div class="card-header py-3">
                            <h9 class="my-0 fw-normal">${item.name_i18n.ja}</h9>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled mt-3 mb-4">
                            <li><img style="width:70%" src="img/items/${item.itemId}.png"></li>
                            </ul>
                        </div>
                    `;

                    content.appendChild(itemDiv);
                }
            });
        })
        .catch(error => console.error('Error:', error));
});