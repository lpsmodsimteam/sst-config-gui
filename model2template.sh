#!/bin/bash

if [[ $1 == "" || $2 == "" ]]; then
	exit
fi

model=${1%/}
template=${2%/}

cp -r $model $template
cd $template
mv tests/* .
rmdir tests
files=$(ls | tr " " "\n" | grep $model)
newFiles=${files//$model/model}
newNames=${files//$model/<model>}
files=($files)
newFiles=($newFiles)
newNames=($newNames)

echo "Makefile Makefile" > template

for i in $(seq 1 ${#files[@]}); do
	mv ${files[i-1]} ${newFiles[i-1]}
	if [[ "${newFiles[i-1]}" == *.py ]]; then
		echo "${newFiles[i-1]} tests/${newNames[i-1]}" >> template
	else
		echo "${newFiles[i-1]} ${newNames[i-1]}" >> template
	fi
done

find . -type f -exec sed -i "s/$model/<model>/Ig" {} +
